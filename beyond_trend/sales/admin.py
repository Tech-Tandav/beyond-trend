from django.contrib import admin

from beyond_trend.core.admin import BaseModelAdmin
from beyond_trend.core.excel import ExcelExportMixin

from beyond_trend.sales.models import Sale, SaleItem


class SaleItemInline(admin.TabularInline):
    model = SaleItem
    extra = 0
    fields = ["variant", "quantity", "selling_price"]


@admin.register(Sale)
class SaleAdmin(ExcelExportMixin, BaseModelAdmin):
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
    actions = ["archive", "restore", "export_to_excel"]

    excel_export_fields = [
        ("Sale ID", "id"),
        ("Staff", "staff"),
        ("Customer", "customer"),
        ("Subtotal", "subtotal"),
        ("Discount", "discount_amount"),
        ("Total", "total_amount"),
        ("Loyalty Points Used", "loyalty_points_used"),
        ("Loyalty Points Earned", "loyalty_points_earned"),
        ("Notes", "notes"),
        ("Created At", "created_at"),
    ]
    excel_sheet_name = "Sales"
    excel_filename_prefix = "sales"

    def get_excel_sheets(self, request, queryset):
        return super().get_excel_sheets(
            request, queryset.select_related("staff", "customer")
        )


@admin.register(SaleItem)
class SaleItemAdmin(BaseModelAdmin):
    list_display = ["sale", "product", "quantity", "selling_price"]
    search_fields = ["product__name", "product__barcode", "id"]
