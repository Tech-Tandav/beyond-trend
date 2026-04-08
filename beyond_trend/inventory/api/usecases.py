from django.db import transaction
from rest_framework.exceptions import NotFound, ValidationError

from beyond_trend.core.usecases import BaseUseCase

from beyond_trend.inventory.models import InventoryLog, Product


class CheckInUseCase(BaseUseCase):
    def __init__(self, product_id, quantity, notes, staff):
        self._product_id = product_id
        self._quantity = quantity
        self._notes = notes
        self._staff = staff
        self._product = None

    def is_valid(self):
        try:
            self._product = Product.objects.select_for_update().get(id=self._product_id)
        except Product.DoesNotExist:
            raise NotFound("Product not found.")

    @transaction.atomic
    def execute(self):
        self.is_valid()
        return self._factory()

    def _factory(self):
        self._product.quantity += self._quantity
        self._product.save(update_fields=["quantity"])

        InventoryLog.objects.create(
            product=self._product,
            action=InventoryLog.CHECK_IN,
            quantity=self._quantity,
            staff=self._staff,
            notes=self._notes,
        )

        return {
            "detail": "Stock checked in successfully.",
            "product": str(self._product),
            "new_quantity": self._product.quantity,
        }


class CheckOutUseCase(BaseUseCase):
    def __init__(self, product_id, quantity, notes, staff):
        self._product_id = product_id
        self._quantity = quantity
        self._notes = notes
        self._staff = staff
        self._product = None

    def is_valid(self):
        try:
            self._product = Product.objects.select_for_update().get(id=self._product_id)
        except Product.DoesNotExist:
            raise NotFound("Product not found.")

        if self._product.quantity < self._quantity:
            raise ValidationError(
                {"detail": f"Insufficient stock. Available: {self._product.quantity}"}
            )

    @transaction.atomic
    def execute(self):
        self.is_valid()
        return self._factory()

    def _factory(self):
        self._product.quantity -= self._quantity
        self._product.save(update_fields=["quantity"])

        InventoryLog.objects.create(
            product=self._product,
            action=InventoryLog.CHECK_OUT,
            quantity=-self._quantity,
            staff=self._staff,
            notes=self._notes,
        )

        return {
            "detail": "Stock checked out successfully.",
            "product": str(self._product),
            "new_quantity": self._product.quantity,
        }
