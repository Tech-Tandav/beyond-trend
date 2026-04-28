from django.contrib import admin

from beyond_trend.core.admin import BaseModelAdmin, BasePublishModelAdmin
from beyond_trend.core.excel import ExcelExportMixin

from beyond_trend.inventory.models import (
    Brand,
    Category,
    InventoryLog,
    Product,
    ProductImage,
    SubCategory,
    Vendor,
)


@admin.register(Vendor)
class VendorAdmin(BaseModelAdmin):
    list_display = ["name", "slug", "is_archived", "created_at", "contact_info", "pan_number", "vat_number"]
    search_fields = ["name", "id"]
    prepopulated_fields = {"slug": ("name",)}

@admin.register(Brand)
class BrandAdmin(BaseModelAdmin):
    list_display = ["name", "slug", "is_archived", "created_at"]
    search_fields = ["name", "id"]
    prepopulated_fields = {"slug": ("name",)}


class SubCategoryInline(admin.TabularInline):
    model = SubCategory
    extra = 1
    fields = ["name", "slug", "is_active"]
    prepopulated_fields = {"slug": ("name",)}


@admin.register(Category)
class CategoryAdmin(BaseModelAdmin):
    list_display = ["name", "slug", "is_active", "is_archived", "created_at"]
    list_filter = ["is_active", "is_archived"]
    search_fields = ["name", "id"]
    prepopulated_fields = {"slug": ("name",)}
    inlines = [SubCategoryInline]


@admin.register(SubCategory)
class SubCategoryAdmin(BaseModelAdmin):
    list_display = ["name", "category", "slug", "is_active", "is_archived", "created_at"]
    list_filter = ["category", "is_active", "is_archived"]
    search_fields = ["name", "category__name", "id"]
    prepopulated_fields = {"slug": ("name",)}


class ProductImageInline(admin.TabularInline):
    model = ProductImage
    extra = 1
    fields = ["image", "is_primary", "order"]


@admin.register(Product)
class ProductAdmin(ExcelExportMixin, BasePublishModelAdmin):
    list_display = ["brand", "model", "category", "subcategory", "colors_display", "sizes_display", "quantity", "is_published", "is_archived", "created_at"]
    list_filter = ["brand", "category", "subcategory", "is_published", "is_archived"]
    search_fields = ["model", "brand__name", "category__name", "subcategory__name", "id"]
    autocomplete_fields = ["category", "subcategory", "brand", "vendor"]
    actions = ["archive", "restore", "publish", "hide", "export_to_excel"]
    inlines = [ProductImageInline]

    @admin.display(description="Size")
    def sizes_display(self, obj):
        return ", ".join(obj.size) if obj.size else "-"

    @admin.display(description="Color")
    def colors_display(self, obj):
        return ", ".join(obj.color) if obj.color else "-"

    excel_export_fields = [
        ("Product ID", "id"),
        ("Brand", "brand__name"),
        ("Category", "category__name"),
        ("Sub Category", "subcategory__name"),
        ("Model", "model"),
        ("Size", "size_display"),
        ("Color", "color_display"),
        ("Barcode", "barcode"),
        ("Vendor", "vendor__name"),
        ("Selling Price", "selling_price"),
        ("Quantity", "quantity"),
        ("Low Stock Threshold", "low_stock_threshold"),
        ("Published", "is_published"),
        ("Archived", "is_archived"),
        ("Created At", "created_at"),
    ]
    excel_sheet_name = "Products"
    excel_filename_prefix = "products"

    def get_excel_sheets(self, request, queryset):
        return super().get_excel_sheets(
            request, queryset.select_related("brand", "vendor", "category", "subcategory")
        )


@admin.register(InventoryLog)
class InventoryLogAdmin(BaseModelAdmin):
    list_display = [ "action", "quantity", "staff", "created_at"]
    list_filter = ["action", "is_archived"]
    search_fields = ["product__name", "product__barcode", "id"]