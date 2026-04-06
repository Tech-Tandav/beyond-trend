from django.contrib import admin

from beyond_trend.core.admin import BaseModelAdmin, BasePublishModelAdmin

from beyond_trend.inventory.models import Brand, InventoryLog, Product, Stock


@admin.register(Brand)
class BrandAdmin(BaseModelAdmin):
    list_display = ["name", "slug", "is_archived", "created_at"]
    search_fields = ["name", "id"]
    prepopulated_fields = {"slug": ("name",)}


@admin.register(Product)
class ProductAdmin(BasePublishModelAdmin):
    list_display = ["name", "brand",  "is_published", "is_archived", "created_at"]
    list_filter = ["brand",  "is_published", "is_archived"]
    search_fields = ["name", "id"]


@admin.register(Stock)
class StockAdmin(BaseModelAdmin):
    list_display = ["product", "quantity", "low_stock_status", "out_of_stock_status"]
    search_fields = ["product__name", "product__barcode", "id"]

    @admin.display(boolean=True, description="Low Stock")
    def low_stock_status(self, obj):
        return obj.is_low_stock

    @admin.display(boolean=True, description="Out of Stock")
    def out_of_stock_status(self, obj):
        return obj.is_out_of_stock


@admin.register(InventoryLog)
class InventoryLogAdmin(BaseModelAdmin):
    list_display = [ "action", "quantity", "staff", "created_at"]
    list_filter = ["action", "is_archived"]
    search_fields = ["product__name", "product__barcode", "id"]