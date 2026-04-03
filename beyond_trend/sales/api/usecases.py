from django.db import transaction
from rest_framework.exceptions import NotFound, ValidationError

from beyond_trend.core.usecases import BaseUseCase
from beyond_trend.inventory.models import InventoryLog, ProductVariant, Stock
from beyond_trend.loyalty.models import Customer, LoyaltySettings, LoyaltyTransaction

from beyond_trend.sales.models import Sale, SaleItem


class CheckoutUseCase(BaseUseCase):
    def __init__(self, data, staff):
        self._data = data
        self._staff = staff
        self._customer = None
        self._variants = {}
        self._stocks = {}
        self._loyalty_settings = None
        self._subtotal = 0
        self._discount_amount = 0
        self._total_amount = 0
        self._loyalty_points_used = data.get("loyalty_points_used", 0)

    def is_valid(self):
        customer_id = self._data.get("customer_id")
        if customer_id:
            try:
                self._customer = Customer.objects.get(id=customer_id)
            except Customer.DoesNotExist:
                raise NotFound("Customer not found.")

        for item in self._data["items"]:
            vid = item["variant_id"]
            try:
                variant = ProductVariant.objects.get(id=vid)
            except ProductVariant.DoesNotExist:
                raise NotFound(f"Variant {vid} not found.")
            try:
                stock = Stock.objects.get(variant=variant)
            except Stock.DoesNotExist:
                raise ValidationError({"detail": f"No stock for variant: {variant}"})
            if stock.quantity < item["quantity"]:
                raise ValidationError(
                    {
                        "detail": f"Insufficient stock for {variant}. "
                        f"Available: {stock.quantity}, Requested: {item['quantity']}"
                    }
                )
            self._variants[str(vid)] = variant
            self._stocks[str(vid)] = stock

        self._subtotal = sum(
            item["quantity"] * item["selling_price"] for item in self._data["items"]
        )

        if self._loyalty_points_used > 0 and self._customer:
            self._loyalty_settings = LoyaltySettings.objects.first()
            if not self._loyalty_settings:
                raise ValidationError({"detail": "Loyalty settings not configured."})
            if self._customer.total_points < self._loyalty_points_used:
                raise ValidationError(
                    {"detail": f"Insufficient loyalty points. Available: {self._customer.total_points}"}
                )
            self._discount_amount = self._loyalty_points_used * self._loyalty_settings.point_value_npr

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

        for item in self._data["items"]:
            vid = str(item["variant_id"])
            variant = self._variants[vid]
            stock = self._stocks[vid]

            SaleItem.objects.create(
                sale=sale,
                variant=variant,
                quantity=item["quantity"],
                selling_price=item["selling_price"],
            )

            stock.quantity -= item["quantity"]
            stock.save(update_fields=["quantity"])

            InventoryLog.objects.create(
                variant=variant,
                action=InventoryLog.CHECK_OUT,
                quantity=-item["quantity"],
                staff=self._staff,
                notes=f"Sale #{str(sale.id)[:8]}",
            )

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
