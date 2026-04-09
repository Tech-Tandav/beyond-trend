from django.conf import settings
from django.db import models
from django.utils.translation import gettext_lazy as _

from beyond_trend.core.models import BaseModel


class Sale(BaseModel):
    staff = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name="sales",
    )
    subtotal = models.DecimalField(_("Subtotal"), max_digits=12, decimal_places=2)
    discount_amount = models.DecimalField(
        _("Discount Amount"), max_digits=12, decimal_places=2, default=0
    )
    total_amount = models.DecimalField(_("Total Amount"), max_digits=12, decimal_places=2)
    notes = models.TextField(_("Notes"), blank=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"Sale #{str(self.id)[:8]} — NPR {self.total_amount}"


class SaleItem(BaseModel):
    sale = models.ForeignKey(
        Sale,
        on_delete=models.CASCADE,
        related_name="items",
    )
    product = models.ForeignKey(
        "inventory.Product",
        on_delete=models.CASCADE,
        related_name="sale_items",
    )
    quantity = models.PositiveIntegerField(_("Quantity"))
    selling_price = models.DecimalField(_("Selling Price"), max_digits=10, decimal_places=2)

    class Meta:
        ordering = ["sale"]

    def __str__(self):
        return f"{self.product} x{self.quantity} @ NPR {self.selling_price}"

    @property
    def total(self):
        return self.quantity * self.selling_price
