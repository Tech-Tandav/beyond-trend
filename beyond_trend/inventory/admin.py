from django.contrib import admin

from beyond_trend.core.admin import BaseModelAdmin, BasePublishModelAdmin

from beyond_trend.inventory.models import Brand, Category, InventoryLog, Product, ProductVariant, Stock, ShoeProduct


@admin.register(Brand)
class BrandAdmin(BaseModelAdmin):
    list_display = ["name", "slug", "is_archived", "created_at"]
    search_fields = ["name", "id"]
    prepopulated_fields = {"slug": ("name",)}


@admin.register(Category)
class CategoryAdmin(BaseModelAdmin):
    list_display = ["name", "slug", "is_archived", "created_at"]
    search_fields = ["name", "id"]
    prepopulated_fields = {"slug": ("name",)}


class ProductVariantInline(admin.TabularInline):
    model = ProductVariant
    extra = 1
    fields = ["size", "color", "barcode", "cost_price", "selling_price", "low_stock_threshold"]
    readonly_fields = ["barcode"]


@admin.register(Product)
class ProductAdmin(BasePublishModelAdmin):
    list_display = ["name", "brand", "category", "is_published", "is_archived", "created_at"]
    list_filter = ["brand", "category", "is_published", "is_archived"]
    search_fields = ["name", "id"]
    inlines = [ProductVariantInline]


@admin.register(ProductVariant)
class ProductVariantAdmin(BaseModelAdmin):
    list_display = ["product", "size", "color", "barcode", "cost_price", "selling_price"]
    list_filter = ["product__brand", "product__category", "is_archived"]
    search_fields = ["product__name", "barcode", "size", "color", "id"]
    readonly_fields = ["barcode", "created_at", "updated_at"]


@admin.register(Stock)
class StockAdmin(BaseModelAdmin):
    list_display = ["variant", "quantity", "low_stock_status", "out_of_stock_status"]
    search_fields = ["variant__product__name", "variant__barcode", "id"]

    @admin.display(boolean=True, description="Low Stock")
    def low_stock_status(self, obj):
        return obj.is_low_stock

    @admin.display(boolean=True, description="Out of Stock")
    def out_of_stock_status(self, obj):
        return obj.is_out_of_stock


@admin.register(InventoryLog)
class InventoryLogAdmin(BaseModelAdmin):
    list_display = ["variant", "action", "quantity", "staff", "created_at"]
    list_filter = ["action", "is_archived"]
    search_fields = ["variant__product__name", "variant__barcode", "id"]


@admin.register(ShoeProduct)
class ShoeProductAdmin(BasePublishModelAdmin):
    list_display = [ "brand_name", "size", "color", "quantity", "selling_price", "is_archived", "created_at"]
    list_filter = [ "is_archived"]
    search_fields = ["brand_name", "barcode", "id"]
    readonly_fields = ["barcode"]