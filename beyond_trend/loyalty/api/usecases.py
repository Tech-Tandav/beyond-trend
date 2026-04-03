from django.db import transaction
from rest_framework.exceptions import NotFound, ValidationError

from beyond_trend.core.usecases import BaseUseCase

from ..models import Customer, LoyaltySettings, LoyaltyTransaction


class RedeemPointsUseCase(BaseUseCase):
    def __init__(self, customer_id, points, notes):
        self._customer_id = customer_id
        self._points = points
        self._notes = notes
        self._customer = None
        self._settings = None

    def is_valid(self):
        try:
            self._customer = Customer.objects.get(id=self._customer_id)
        except Customer.DoesNotExist:
            raise NotFound("Customer not found.")

        if self._customer.total_points < self._points:
            raise ValidationError(
                {"detail": f"Insufficient points. Available: {self._customer.total_points}"}
            )

        self._settings = LoyaltySettings.objects.first()
        if not self._settings:
            raise ValidationError({"detail": "Loyalty settings not configured."})

    @transaction.atomic
    def execute(self):
        self.is_valid()
        return self._factory()

    def _factory(self):
        discount = self._points * self._settings.point_value_npr

        self._customer.total_points -= self._points
        self._customer.save(update_fields=["total_points"])

        LoyaltyTransaction.objects.create(
            customer=self._customer,
            points=-self._points,
            type=LoyaltyTransaction.REDEEMED,
            notes=self._notes,
        )

        return {
            "detail": "Points redeemed successfully.",
            "points_redeemed": self._points,
            "discount_amount": float(discount),
            "remaining_points": self._customer.total_points,
        }
