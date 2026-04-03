from django.db import transaction
from rest_framework.exceptions import NotFound, ValidationError

from beyond_trend.core.usecases import BaseUseCase

from beyond_trend.inventory.models import InventoryLog, ProductVariant, Stock


class CheckInUseCase(BaseUseCase):
    def __init__(self, variant_id, quantity, notes, staff):
        self._variant_id = variant_id
        self._quantity = quantity
        self._notes = notes
        self._staff = staff
        self._variant = None

    def is_valid(self):
        try:
            self._variant = ProductVariant.objects.get(id=self._variant_id)
        except ProductVariant.DoesNotExist:
            raise NotFound("Variant not found.")

    @transaction.atomic
    def execute(self):
        self.is_valid()
        return self._factory()

    def _factory(self):
        stock, _ = Stock.objects.get_or_create(variant=self._variant)
        stock.quantity += self._quantity
        stock.save(update_fields=["quantity"])

        InventoryLog.objects.create(
            variant=self._variant,
            action=InventoryLog.CHECK_IN,
            quantity=self._quantity,
            staff=self._staff,
            notes=self._notes,
        )

        return {
            "detail": "Stock checked in successfully.",
            "variant": str(self._variant),
            "new_quantity": stock.quantity,
        }


class CheckOutUseCase(BaseUseCase):
    def __init__(self, variant_id, quantity, notes, staff):
        self._variant_id = variant_id
        self._quantity = quantity
        self._notes = notes
        self._staff = staff
        self._variant = None
        self._stock = None

    def is_valid(self):
        try:
            self._variant = ProductVariant.objects.get(id=self._variant_id)
        except ProductVariant.DoesNotExist:
            raise NotFound("Variant not found.")

        try:
            self._stock = Stock.objects.get(variant=self._variant)
        except Stock.DoesNotExist:
            raise ValidationError({"detail": "No stock record for this variant."})

        if self._stock.quantity < self._quantity:
            raise ValidationError(
                {"detail": f"Insufficient stock. Available: {self._stock.quantity}"}
            )

    @transaction.atomic
    def execute(self):
        self.is_valid()
        return self._factory()

    def _factory(self):
        self._stock.quantity -= self._quantity
        self._stock.save(update_fields=["quantity"])

        InventoryLog.objects.create(
            variant=self._variant,
            action=InventoryLog.CHECK_OUT,
            quantity=-self._quantity,
            staff=self._staff,
            notes=self._notes,
        )

        return {
            "detail": "Stock checked out successfully.",
            "variant": str(self._variant),
            "new_quantity": self._stock.quantity,
        }
