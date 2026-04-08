from django.db import models
from django.utils.translation import gettext_lazy as _

from beyond_trend.core.models import BaseModel


class Customer(BaseModel):
    REDEEM_THRESHOLD = 500

    name = models.CharField(_("Name"), max_length=255)
    email = models.EmailField(_("Email"), unique=True)
    phone = models.CharField(_("Phone"), max_length=20, blank=True)
    total_points = models.PositiveIntegerField(_("Total Points"), default=0)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return f"{self.name} ({self.email})"

    @property
    def is_redeemable(self):
        return self.total_points >= self.REDEEM_THRESHOLD


class LoyaltyTransaction(BaseModel):
    EARNED = "earned"
    REDEEMED = "redeemed"
    TYPE_CHOICES = [
        (EARNED, "Earned"),
        (REDEEMED, "Redeemed"),
    ]

    customer = models.ForeignKey(
        Customer,
        on_delete=models.CASCADE,
        related_name="transactions",
    )
    points = models.IntegerField(_("Points"))  # positive=earned, negative=redeemed
    type = models.CharField(_("Type"), max_length=10, choices=TYPE_CHOICES)
    sale = models.ForeignKey(
        "sales.Sale",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="loyalty_transactions",
    )
    notes = models.TextField(_("Notes"), blank=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.customer.name} — {self.get_type_display()} {abs(self.points)} pts"


class LoyaltySettings(BaseModel):
    """Singleton model — only one row allowed."""

    points_per_100_npr = models.PositiveIntegerField(
        _("Points per NPR 100"),
        default=1,
        help_text="Number of loyalty points earned for every NPR 100 spent.",
    )
    point_value_npr = models.DecimalField(
        _("Point Value (NPR)"),
        max_digits=6,
        decimal_places=2,
        default=1.00,
        help_text="NPR value of 1 loyalty point when redeemed.",
    )

    class Meta:
        verbose_name = "Loyalty Settings"
        verbose_name_plural = "Loyalty Settings"

    def __str__(self):
        return "Loyalty Settings"

    @classmethod
    def get(cls):
        obj, _ = cls.objects.get_or_create(
            pk=cls.objects.first().pk if cls.objects.exists() else None,
        )
        return obj