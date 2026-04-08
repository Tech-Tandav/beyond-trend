from django.db import transaction
from django.shortcuts import get_object_or_404

from rest_framework.exceptions import NotFound, ValidationError

from beyond_trend.core.usecases import BaseUseCase
from beyond_trend.inventory.models import InventoryLog, Product
from beyond_trend.loyalty.models import Customer, LoyaltySettings, LoyaltyTransaction
from beyond_trend.orders.models import Order

from beyond_trend.sales.models import Sale, SaleItem



class CheckoutUseCase(BaseUseCase):
    def __init__(self, data, staff):
        self._data = data
        self._staff = staff
        self._customer = None
        self._order = None
        self._items = []  # normalized list of {"product": Product, "quantity": int, "selling_price": Decimal}
        self._products = {}
        self._loyalty_settings = None
        self._subtotal = 0
        self._discount_amount = 0
        self._total_amount = 0
        self._redeem = data.get("redeem", False)
        self._loyalty_points_used = 0

    def is_valid(self):
        phone_number = (self._data.get("phone_number") or "").strip()
        if phone_number:
            self._customer = Customer.objects.filter(phone=phone_number).first()
            if not self._customer:
                raise NotFound(f"Customer with phone {phone_number} not found.")

        order_id = self._data.get("order_id")
        if order_id:
            try:
                self._order = Order.objects.prefetch_related("items__product").get(id=order_id)
            except Order.DoesNotExist:
                raise NotFound(f"Order {order_id} not found.")
            if self._order.status in (Order.DELIVERED, Order.CANCELLED):
                raise ValidationError(
                    {"detail": f"Cannot checkout an order in '{self._order.status}' status."}
                )
            if not self._order.items.exists():
                raise ValidationError({"detail": "Order has no items to checkout."})

            # FE may override per-product selling prices on checkout.
            price_overrides = {
                str(i["product_id"]): i["selling_price"]
                for i in (self._data.get("items") or [])
            }

            # Stock was already decremented when the order was created — don't re-check.
            for order_item in self._order.items.all():
                pid = str(order_item.product_id)
                self._items.append({
                    "product": order_item.product,
                    "quantity": order_item.quantity,
                    "selling_price": price_overrides.get(pid, order_item.price),
                })
                self._products[pid] = order_item.product

            if self._customer is None and self._order.loyalty_customer_id:
                self._customer = self._order.loyalty_customer
            if self._customer is None and self._order.phone:
                self._customer = Customer.objects.filter(phone=self._order.phone).first()
        else:
            for item in self._data["items"]:
                vid = item["product_id"]
                try:
                    product = Product.objects.get(id=vid)
                except Product.DoesNotExist:
                    raise NotFound(f"product {vid} not found.")
                if product.quantity < item["quantity"]:
                    raise ValidationError(
                        {
                            "detail": f"Insufficient stock for {product}. "
                            f"Available: {product.quantity}, Requested: {item['quantity']}"
                        }
                    )
                self._products[str(vid)] = product
                self._items.append({
                    "product": product,
                    "quantity": item["quantity"],
                    "selling_price": item["selling_price"],
                })

        self._subtotal = sum(
            item["quantity"] * item["selling_price"] for item in self._items
        )

        if self._redeem:
            if not self._customer:
                raise ValidationError({"detail": "Cannot redeem points without a customer."})
            if not self._customer.is_redeemable:
                raise ValidationError(
                    {"detail": f"Customer needs at least {Customer.REDEEM_THRESHOLD} points to redeem. "
                               f"Available: {self._customer.total_points}"}
                )
            self._loyalty_settings = LoyaltySettings.objects.first()
            if not self._loyalty_settings:
                raise ValidationError({"detail": "Loyalty settings not configured."})

            # Auto-redeem all available points, capped so discount doesn't exceed subtotal.
            point_value = self._loyalty_settings.point_value_npr
            max_points_for_bill = int(self._subtotal // point_value) if point_value else 0
            self._loyalty_points_used = min(self._customer.total_points, max_points_for_bill)
            self._discount_amount = self._loyalty_points_used * point_value

        self._total_amount = self._subtotal - self._discount_amount

    @transaction.atomic
    def execute(self):
        self.is_valid()
        return self._factory()

    def _factory(self):
        sale = Sale.objects.create(
            staff=self._staff,
            customer=self._customer,
            subtotal=self._subtotal,
            discount_amount=self._discount_amount,
            total_amount=self._total_amount,
            loyalty_points_used=self._loyalty_points_used,
            notes=self._data.get("notes", ""),
        )

        for item in self._items:
            product = item["product"]

            SaleItem.objects.create(
                sale=sale,
                product=product,
                quantity=item["quantity"],
                selling_price=item["selling_price"],
            )

            # Stock + inventory log were already handled at order creation time;
            # only decrement here for direct (non-order) checkouts.
            if self._order is None:
                locked = Product.objects.select_for_update().get(pk=product.pk)
                locked.quantity -= item["quantity"]
                locked.save(update_fields=["quantity"])

                InventoryLog.objects.create(
                    product=locked,
                    action=InventoryLog.CHECK_OUT,
                    quantity=-item["quantity"],
                    staff=self._staff,
                    notes=f"Sale #{str(sale.id)[:8]}",
                )

        if self._order is not None:
            # Sync any selling-price overrides applied at checkout back onto the
            # order's line items, then refresh the order total.
            price_by_product = {
                str(item["product"].id): item["selling_price"] for item in self._items
            }
            order_total = 0
            for order_item in self._order.items.all():
                new_price = price_by_product.get(str(order_item.product_id))
                if new_price is not None and new_price != order_item.price:
                    order_item.price = new_price
                    order_item.save(update_fields=["price"])
                order_total += order_item.price * order_item.quantity

            self._order.total_amount = order_total
            # Order has been fulfilled by this sale — mark it delivered.
            self._order.status = Order.DELIVERED
            self._order.save(update_fields=["status", "total_amount"])

        if self._customer:
            if not self._loyalty_settings:
                self._loyalty_settings = LoyaltySettings.objects.first()

            points_earned = 0
            if self._loyalty_settings:
                points_earned = int(float(self._total_amount) / 100 * self._loyalty_settings.points_per_100_npr)

            if self._loyalty_points_used > 0:
                self._customer.total_points -= self._loyalty_points_used
                LoyaltyTransaction.objects.create(
                    customer=self._customer,
                    points=-self._loyalty_points_used,
                    type=LoyaltyTransaction.REDEEMED,
                    sale=sale,
                    notes="Points redeemed at checkout",
                )

            if points_earned > 0:
                self._customer.total_points += points_earned
                LoyaltyTransaction.objects.create(
                    customer=self._customer,
                    points=points_earned,
                    type=LoyaltyTransaction.EARNED,
                    sale=sale,
                    notes="Points earned from purchase",
                )

            self._customer.save(update_fields=["total_points"])
            sale.loyalty_points_earned = points_earned
            sale.save(update_fields=["loyalty_points_earned"])

        return sale
