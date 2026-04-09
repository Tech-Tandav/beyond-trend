from decimal import Decimal

from django.conf import settings
from django.db import models
from django.utils.translation import gettext_lazy as _

from beyond_trend.core.models import BaseModel


class LoyaltyTier(models.TextChoices):
    BRONZE = "bronze", _("Bronze")
    SILVER = "silver", _("Silver")
    GOLD = "gold", _("Gold")
    PLATINUM = "platinum", _("Platinum")


# Points earned per NPR 100 spent
POINTS_PER_100 = 1

# Tier thresholds (total spend in NPR)
TIER_THRESHOLDS = {
    LoyaltyTier.BRONZE: Decimal("0"),
    LoyaltyTier.SILVER: Decimal("10000"),
    LoyaltyTier.GOLD: Decimal("50000"),
    LoyaltyTier.PLATINUM: Decimal("100000"),
}

# Tier discount percentages
TIER_DISCOUNTS = {
    LoyaltyTier.BRONZE: Decimal("0"),
    LoyaltyTier.SILVER: Decimal("2"),
    LoyaltyTier.GOLD: Decimal("5"),
    LoyaltyTier.PLATINUM: Decimal("8"),
}


class Customer(BaseModel):
    name = models.CharField(_("Full Name"), max_length=255)
    phone = models.CharField(_("Phone Number"), max_length=20, unique=True)
    email = models.EmailField(_("Email"), blank=True)
    address = models.TextField(_("Address"), blank=True)

    tier = models.CharField(
        _("Loyalty Tier"),
        max_length=20,
        choices=LoyaltyTier.choices,
        default=LoyaltyTier.BRONZE,
    )
    total_points = models.PositiveIntegerField(_("Total Points"), default=0)
    redeemed_points = models.PositiveIntegerField(_("Redeemed Points"), default=0)
    total_spend = models.DecimalField(
        _("Total Spend (NPR)"), max_digits=12, decimal_places=2, default=0
    )

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.name} ({self.phone})"

    @property
    def available_points(self):
        return self.total_points - self.redeemed_points

    @property
    def tier_discount(self):
        return TIER_DISCOUNTS.get(self.tier, Decimal("0"))

    def recalculate_tier(self):
        new_tier = LoyaltyTier.BRONZE
        for tier, threshold in sorted(
            TIER_THRESHOLDS.items(), key=lambda x: x[1], reverse=True
        ):
            if self.total_spend >= threshold:
                new_tier = tier
                break
        if self.tier != new_tier:
            self.tier = new_tier
            self.save(update_fields=["tier"])
        return new_tier

    def earn_points(self, amount):
        """Award points based on purchase amount. Returns points earned."""
        points = int(amount / 100) * POINTS_PER_100
        if points > 0:
            self.total_points += points
            self.total_spend += amount
            self.save(update_fields=["total_points", "total_spend"])
            self.recalculate_tier()
        return points

    def redeem_points(self, points):
        """Redeem points. Returns True if successful."""
        if points > self.available_points:
            return False
        self.redeemed_points += points
        self.save(update_fields=["redeemed_points"])
        return True


class LoyaltyTransaction(BaseModel):
    EARN = "earn"
    REDEEM = "redeem"
    ADJUSTMENT = "adjustment"
    TRANSACTION_TYPES = [
        (EARN, _("Earn")),
        (REDEEM, _("Redeem")),
        (ADJUSTMENT, _("Adjustment")),
    ]

    customer = models.ForeignKey(
        Customer,
        on_delete=models.CASCADE,
        related_name="transactions",
    )
    transaction_type = models.CharField(
        _("Type"), max_length=20, choices=TRANSACTION_TYPES
    )
    points = models.IntegerField(
        _("Points"),
        help_text=_("Positive for earn, negative for redeem"),
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
