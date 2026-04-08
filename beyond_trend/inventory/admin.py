from django.contrib import admin

from beyond_trend.core.admin import BaseModelAdmin, BasePublishModelAdmin
from beyond_trend.core.excel import ExcelExportMixin

from beyond_trend.inventory.models import Vendor, Brand, InventoryLog, Product


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


@admin.register(Product)
class ProductAdmin(ExcelExportMixin, BasePublishModelAdmin):
    list_display = ["brand", "model", "color", "size", "quantity", "is_published", "is_archived", "created_at"]
    list_filter = ["brand", "is_published", "is_archived"]
    search_fields = ["model", "brand__name", "id"]
    actions = ["archive", "restore", "publish", "hide", "export_to_excel"]

    excel_export_fields = [
        ("Product ID", "id"),
        ("Brand", "brand__name"),
        ("Model", "model"),
        ("Size", "size"),
        ("Color", "color"),
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
            request, queryset.select_related("brand", "vendor")
        )


@admin.register(InventoryLog)
class InventoryLogAdmin(BaseModelAdmin):
    list_display = [ "action", "quantity", "staff", "created_at"]
    list_filter = ["action", "is_archived"]
    search_fields = ["product__name", "product__barcode", "id"]