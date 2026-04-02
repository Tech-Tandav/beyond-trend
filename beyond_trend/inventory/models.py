import uuid

from django.conf import settings
from django.db import models
from django.utils.translation import gettext_lazy as _

from beyond_trend.core.models import BaseModel, BaseModelWithSlug


class Brand(BaseModelWithSlug):
    name = models.CharField(_("Brand Name"), max_length=100, unique=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name


class Category(BaseModelWithSlug):
    name = models.CharField(_("Category Name"), max_length=100, unique=True)

    class Meta:
        ordering = ["name"]
        verbose_name_plural = "Categories"

    def __str__(self):
        return self.name


class Product(BaseModelWithSlug):
    name = models.CharField(_("Product Name"), max_length=255)
    brand = models.ForeignKey(
        Brand,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="products",
    )
    category = models.ForeignKey(
        Category,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="products",
    )
    description = models.TextField(_("Description"), blank=True)
    image = models.ImageField(_("Image"), upload_to="products/", null=True, blank=True)
    is_published = models.BooleanField(_("Published"), default=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name


class ProductVariant(BaseModel):
    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name="variants",
    )
    size = models.CharField(_("Size"), max_length=20)
    color = models.CharField(_("Color"), max_length=50)
    barcode = models.CharField(_("Barcode"), max_length=100, unique=True, blank=True)
    cost_price = models.DecimalField(_("Cost Price"), max_digits=10, decimal_places=2)
    selling_price = models.DecimalField(_("Selling Price"), max_digits=10, decimal_places=2)
    low_stock_threshold = models.PositiveIntegerField(_("Low Stock Threshold"), default=5)

    class Meta:
        unique_together = [["product", "size", "color"]]
        ordering = ["product", "size", "color"]

    def __str__(self):
        return f"{self.product.name} - {self.size} / {self.color}"

    def save(self, *args, **kwargs):
        if not self.barcode:
            self.barcode = uuid.uuid4().hex[:12].upper()
        super().save(*args, **kwargs)


class Stock(BaseModel):
    variant = models.OneToOneField(
        ProductVariant,
        on_delete=models.CASCADE,
        related_name="stock",
    )
    quantity = models.PositiveIntegerField(_("Quantity"), default=0)

    class Meta:
        verbose_name = "Stock"
        verbose_name_plural = "Stock"

    def __str__(self):
        return f"{self.variant} — {self.quantity} units"

    @property
    def is_low_stock(self):
        return 0 < self.quantity <= self.variant.low_stock_threshold

    @property
    def is_out_of_stock(self):
        return self.quantity == 0


class InventoryLog(BaseModel):
    CHECK_IN = "check_in"
    CHECK_OUT = "check_out"
    ADJUSTMENT = "adjustment"
    ACTION_CHOICES = [
        (CHECK_IN, "Check In"),
        (CHECK_OUT, "Check Out"),
        (ADJUSTMENT, "Adjustment"),
    ]

    variant = models.ForeignKey(
        ProductVariant,
        on_delete=models.CASCADE,
        related_name="inventory_logs",
    )
    action = models.CharField(_("Action"), max_length=20, choices=ACTION_CHOICES)
    quantity = models.IntegerField(_("Quantity"))  # positive=in, negative=out
    staff = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name="inventory_logs",
    )
    notes = models.TextField(_("Notes"), blank=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.get_action_display()} | {self.variant} | {self.quantity}"
