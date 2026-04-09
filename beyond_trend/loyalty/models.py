from decimal import Decimal

from django.conf import settings
from django.db import models
from django.utils.translation import gettext_lazy as _

from beyond_trend.core.models import BaseModel


# Only products in this subcategory earn loyalty points
LOYALTY_ELIGIBLE_SUBCATEGORY_SLUG = "sneakers"

# Flat points earned per sneaker sale
POINTS_PER_SNEAKER_SALE = 100

# Points threshold that triggers a discount on the next transaction
DISCOUNT_THRESHOLD = 500

# Discount percentage applied on the transaction after reaching threshold
DISCOUNT_PERCENTAGE = Decimal("10")


class Customer(BaseModel):
    name = models.CharField(_("Full Name"), max_length=255)
    phone = models.CharField(_("Phone Number"), max_length=20, unique=True)
    email = models.EmailField(_("Email"), blank=True)
    address = models.TextField(_("Address"), blank=True)

    total_points = models.PositiveIntegerField(_("Total Points"), default=0)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.name} ({self.phone})"

    @property
    def is_discount_eligible(self):
        """True when customer has accumulated enough points for a discount."""
        return self.total_points >= DISCOUNT_THRESHOLD

    def earn_points(self):
        """
        Award flat points for a sneaker purchase.
        If customer has reached the threshold, apply discount and reset.
        Returns (points_earned, discount_percent).
        """
        discount_percent = Decimal("0")

        if self.total_points >= DISCOUNT_THRESHOLD:
            discount_percent = DISCOUNT_PERCENTAGE
            self.total_points = 0  # reset cycle

        self.total_points += POINTS_PER_SNEAKER_SALE
        self.save(update_fields=["total_points"])
        return POINTS_PER_SNEAKER_SALE, discount_percent


class LoyaltyTransaction(BaseModel):
    EARN = "earn"
    TRANSACTION_TYPES = [
        (EARN, _("Earn")),
    ]

    customer = models.ForeignKey(
        Customer,
        on_delete=models.CASCADE,
        related_name="transactions",
    )
    transaction_type = models.CharField(
        _("Type"), max_length=20, choices=TRANSACTION_TYPES, default=EARN
    )
    points = models.IntegerField(
        _("Points"),
        help_text=_("Points earned in this transaction"),
    )
    discount_applied = models.DecimalField(
        _("Discount %"),
        max_digits=5,
        decimal_places=2,
        default=0,
        help_text=_("Discount percentage applied on this transaction (0 if none)"),
    )
    sale = models.ForeignKey(
        "sales.Sale",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="loyalty_transactions",
    )
    staff = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="loyalty_transactions",
    )
    notes = models.TextField(_("Notes"), blank=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.customer.name} — {self.transaction_type} {self.points} pts"
