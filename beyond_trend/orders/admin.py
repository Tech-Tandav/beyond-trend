from django.contrib import admin

from beyond_trend.core.admin import BaseModelAdmin
from beyond_trend.core.excel import ExcelExportMixin

from beyond_trend.orders.models import Order, OrderItem, PreOrder


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    fields = ["product", "quantity", "price"]


@admin.register(Order)
class OrderAdmin(ExcelExportMixin, BaseModelAdmin):
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
    actions = ["archive", "restore", "export_to_excel"]

    excel_export_fields = [
        ("Order ID", "id"),
        ("Customer", "customer_name"),
        ("Email", "email"),
        ("Phone", "phone"),
        ("Status", "get_status_display"),
        ("Total Amount", "total_amount"),
        ("Notes", "notes"),
        ("Loyalty Customer", "loyalty_customer"),
        ("Created At", "created_at"),
    ]
    excel_sheet_name = "Orders"
    excel_filename_prefix = "orders"

    def get_excel_sheets(self, request, queryset):
        sheets = super().get_excel_sheets(
            request, queryset.prefetch_related("items__product")
        )
        item_rows = []
        for order in queryset:
            for item in order.items.all():
                item_rows.append(
                    [
                        str(order.id),
                        order.customer_name,
                        str(item.product),
                        item.quantity,
                        item.price,
                        item.total,
                    ]
                )
        sheets.append(
            {
                "name": "Order Items",
                "headers": [
                    "Order ID",
                    "Customer",
                    "Product",
                    "Quantity",
                    "Price",
                    "Line Total",
                ],
                "rows": item_rows,
            }
        )
        return sheets


@admin.register(PreOrder)
class PreOrderAdmin(ExcelExportMixin, BaseModelAdmin):
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
    actions = ["archive", "restore", "export_to_excel"]

    excel_export_fields = [
        ("Pre-Order ID", "id"),
        ("Customer", "customer_name"),
        ("Email", "email"),
        ("Phone", "phone"),
        ("Product Name", "product_name"),
        ("Brand", "brand"),
        ("Size", "size"),
        ("Color", "color"),
        ("Status", "get_status_display"),
        ("Notes", "notes"),
        ("Created At", "created_at"),
    ]
    excel_sheet_name = "Pre-Orders"
    excel_filename_prefix = "pre_orders"