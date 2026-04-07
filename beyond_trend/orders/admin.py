from django.contrib import admin

from beyond_trend.core.admin import BaseModelAdmin

from beyond_trend.orders.models import Order, OrderItem, PreOrder


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    fields = ["product", "quantity", "price"]


@admin.register(Order)
class OrderAdmin(BaseModelAdmin):
    list_display = [
        "id",
        "customer_name",
        "email",
        "phone",
        "status",
        "total_amount",
        "created_at",
    ]
    list_filter = ["status", "is_archived"]
    search_fields = ["customer_name", "email", "phone", "id"]
    inlines = [OrderItemInline]


@admin.register(PreOrder)
class PreOrderAdmin(BaseModelAdmin):
    list_display = [
        "customer_name",
        "email",
        "product_name",
        "brand",
        "size",
        "color",
        "status",
        "created_at",
    ]
    list_filter = ["status", "is_archived"]
    search_fields = ["customer_name", "email", "product_name", "id"]
