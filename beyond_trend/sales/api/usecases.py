from django.db import transaction

from rest_framework.exceptions import NotFound, ValidationError

from beyond_trend.core.usecases import BaseUseCase
from beyond_trend.inventory.models import InventoryLog, Product
from beyond_trend.orders.models import Order

from beyond_trend.sales.models import Sale, SaleItem


class CheckoutUseCase(BaseUseCase):
    def __init__(self, data, staff):
        self._data = data
        self._staff = staff
        self._order = None
        self._items = []  # normalized list of {"product": Product, "quantity": int, "selling_price": Decimal}
        self._products = {}
        self._subtotal = 0
        self._discount_amount = 0
        self._total_amount = 0

    def is_valid(self):
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
                if "selling_price" in i
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
                    "selling_price": item.get("selling_price", product.selling_price),
                })

        self._subtotal = sum(
            item["quantity"] * item["selling_price"] for item in self._items
        )
        self._total_amount = self._subtotal - self._discount_amount

    @transaction.atomic
    def execute(self):
        self.is_valid()
        return self._factory()

    def _factory(self):
        sale = Sale.objects.create(
            staff=self._staff,
            subtotal=self._subtotal,
            discount_amount=self._discount_amount,
            total_amount=self._total_amount,
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

        return sale
