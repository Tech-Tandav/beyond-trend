from django.db import models
from django.utils.translation import gettext_lazy as _

from beyond_trend.core.models import BaseModel


class Order(BaseModel):
    PENDING = "pending"
    CONFIRMED = "confirmed"
    PROCESSING = "processing"
    READY = "ready"
    DELIVERED = "delivered"
    CANCELLED = "cancelled"
    STATUS_CHOICES = [
        (PENDING, "Pending"),
        (CONFIRMED, "Confirmed"),
        (PROCESSING, "Processing"),
        (READY, "Ready for Pickup"),
        (DELIVERED, "Delivered"),
        (CANCELLED, "Cancelled"),
    ]

    customer_name = models.CharField(_("Customer Name"), max_length=255)
    email = models.EmailField(_("Email"))
    phone = models.CharField(_("Phone"), max_length=20, blank=True)
    status = models.CharField(
        _("Status"), max_length=20, choices=STATUS_CHOICES, default=PENDING
    )
    total_amount = models.DecimalField(
        _("Total Amount"), max_digits=12, decimal_places=2, default=0
    )
    notes = models.TextField(_("Notes"), blank=True)
    loyalty_customer = models.ForeignKey(
        "loyalty.Customer",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="orders",
    )

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"Order #{str(self.id)[:8]} — {self.customer_name}"


class OrderItem(BaseModel):
    order = models.ForeignKey(
        Order,
        on_delete=models.CASCADE,
        related_name="items",
    )
    variant = models.ForeignKey(
        "inventory.ProductVariant",
        on_delete=models.CASCADE,
        related_name="order_items",
    )
    quantity = models.PositiveIntegerField(_("Quantity"))
    price = models.DecimalField(_("Price"), max_digits=10, decimal_places=2)

    def __str__(self):
        return f"{self.variant} x{self.quantity}"

    @property
    def total(self):
        return self.quantity * self.price


class PreOrder(BaseModel):
    PENDING = "pending"
    NOTIFIED = "notified"
    FULFILLED = "fulfilled"
    STATUS_CHOICES = [
        (PENDING, "Pending"),
        (NOTIFIED, "Notified"),
        (FULFILLED, "Fulfilled"),
    ]

    customer_name = models.CharField(_("Customer Name"), max_length=255)
    email = models.EmailField(_("Email"))
    phone = models.CharField(_("Phone"), max_length=20, blank=True)
    product_name = models.CharField(_("Product Name"), max_length=255)
    brand = models.CharField(_("Brand"), max_length=100, blank=True)
    size = models.CharField(_("Size"), max_length=20, blank=True)
    color = models.CharField(_("Color"), max_length=50, blank=True)
    notes = models.TextField(_("Notes"), blank=True)
    status = models.CharField(
        _("Status"), max_length=20, choices=STATUS_CHOICES, default=PENDING
    )

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"Pre-Order: {self.product_name} for {self.customer_name}"
