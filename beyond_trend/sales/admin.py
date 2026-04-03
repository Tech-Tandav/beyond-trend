from django.contrib import admin

from beyond_trend.core.admin import BaseModelAdmin

from beyond_trend.sales.models import Sale, SaleItem


class SaleItemInline(admin.TabularInline):
    model = SaleItem
    extra = 0
    fields = ["variant", "quantity", "selling_price"]


@admin.register(Sale)
class SaleAdmin(BaseModelAdmin):
    list_display = [
        "id",
        "staff",
        "customer",
        "subtotal",
        "discount_amount",
        "total_amount",
        "loyalty_points_earned",
        "loyalty_points_used",
        "created_at",
    ]
    list_filter = ["is_archived"]
    search_fields = ["staff__username", "customer__name", "customer__email", "id"]
    inlines = [SaleItemInline]


@admin.register(SaleItem)
class SaleItemAdmin(BaseModelAdmin):
    list_display = ["sale", "variant", "quantity", "selling_price"]
    search_fields = ["variant__product__name", "variant__barcode", "id"]
