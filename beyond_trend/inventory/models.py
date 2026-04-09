import uuid

from django.conf import settings
from django.db import models
from django.utils.translation import gettext_lazy as _

from beyond_trend.core.models import BaseModel, BaseModelWithSlug


class Vendor(BaseModelWithSlug):
    name = models.CharField(_("Vendor Name"), max_length=255)
    contact_info = models.TextField(_("Contact Information"), blank=True)
    pan_number = models.CharField(_("PAN Number"), max_length=20, blank=True, null=True)
    vat_number = models.CharField(_("VAT Number"), max_length=20, blank=True, null=True)

    def __str__(self):
        return self.name


class Brand(BaseModelWithSlug):
    name = models.CharField(_("Brand Name"), max_length=100, unique=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name


class Category(BaseModelWithSlug):
    name = models.CharField(_("Category Name"), max_length=100, unique=True)
    description = models.TextField(_("Description"), blank=True)
    is_active = models.BooleanField(_("Active"), default=True)

    class Meta:
        verbose_name = _("Category")
        verbose_name_plural = _("Categories")
        ordering = ["name"]

    def __str__(self):
        return self.name


class SubCategory(BaseModelWithSlug):
    category = models.ForeignKey(
        Category,
        on_delete=models.CASCADE,
        related_name="subcategories",
    )
    name = models.CharField(_("Sub Category Name"), max_length=100)
    description = models.TextField(_("Description"), blank=True)
    is_active = models.BooleanField(_("Active"), default=True)

    class Meta:
        verbose_name = _("Sub Category")
        verbose_name_plural = _("Sub Categories")
        ordering = ["category__name", "name"]
        unique_together = ["category", "name"]

    def __str__(self):
        return f"{self.category.name} > {self.name}"


class Product(BaseModelWithSlug):
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
    subcategory = models.ForeignKey(
        SubCategory,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="products",
    )
    model = models.CharField(_("Model"), max_length=255, default="")
    vendor = models.ForeignKey(
        Vendor,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="products",
    )
    description = models.TextField(_("Description"), blank=True)
    is_published = models.BooleanField(_("Published"), default=True)
    is_featured = models.BooleanField(_("Featured"), default=False)
    show_in_website = models.BooleanField(_("Show in Website"), default=True)
    size = models.CharField(_("Size"), max_length=20)
    color = models.CharField(_("Color"), max_length=50)
    barcode = models.CharField(_("Barcode"), max_length=100, unique=True, blank=True)
    cost_price = models.DecimalField(_("Cost Price"), max_digits=10, decimal_places=2, null=True, blank=True)
    selling_price = models.DecimalField(_("Selling Price"), max_digits=10, decimal_places=2, null=True, blank=True)
    quantity = models.PositiveIntegerField(_("Quantity"), default=0)
    low_stock_threshold = models.PositiveIntegerField(_("Low Stock Threshold"), default=5)

    # class Meta:
    #     unique_together = ["brand", "model", "size", "color"]
    #     ordering = ["brand", "model", "size", "color"]

    def __str__(self):
        return f"{self.brand} {self.model} - {self.size} / {self.color}"

    def save(self, *args, **kwargs):
        if not self.barcode:
            self.barcode = uuid.uuid4().hex[:12].upper()
        super().save(*args, **kwargs)

    @property
    def is_low_stock(self):
        return 0 < self.quantity <= self.low_stock_threshold

    @property
    def is_out_of_stock(self):
        return self.quantity == 0


class ProductImage(BaseModel):
    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name="images",
    )
    image = models.ImageField(_("Image"), upload_to="products/")
    is_primary = models.BooleanField(_("Primary"), default=False)
    order = models.PositiveIntegerField(_("Order"), default=0)

    class Meta:
        ordering = ["-is_primary", "order", "created_at"]

    def __str__(self):
        return f"Image for {self.product}"


class InventoryLog(BaseModel):
    CHECK_IN = "check_in"
    CHECK_OUT = "check_out"
    ADJUSTMENT = "adjustment"
    ACTION_CHOICES = [
        (CHECK_IN, "Check In"),
        (CHECK_OUT, "Check Out"),
        (ADJUSTMENT, "Adjustment"),
    ]

    product = models.ForeignKey(
        Product,
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
        return f"{self.get_action_display()} | {self.product} | {self.quantity}"