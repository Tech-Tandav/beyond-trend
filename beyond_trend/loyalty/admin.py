from django.contrib import admin

from beyond_trend.core.admin import BaseModelAdmin
from beyond_trend.loyalty.models import Customer, LoyaltyTransaction


class LoyaltyTransactionInline(admin.TabularInline):
    model = LoyaltyTransaction
    extra = 0
    fields = ["transaction_type", "points", "sale", "staff", "notes", "created_at"]
    readonly_fields = ["created_at"]


@admin.register(Customer)
class CustomerAdmin(BaseModelAdmin):
    list_display = [
        "name",
        "phone",
        "tier",
        "total_points",
        "redeemed_points",
        "available_points",
        "total_spend",
        "created_at",
    ]
    list_filter = ["tier", "is_archived"]
    search_fields = ["name", "phone", "email"]
    inlines = [LoyaltyTransactionInline]
    actions = ["archive", "restore"]
    readonly_fields = ["created_at", "updated_at", "total_points", "redeemed_points", "total_spend", "tier"]

    @admin.display(description="Available Points")
    def available_points(self, obj):
        return obj.available_points


@admin.register(LoyaltyTransaction)
class LoyaltyTransactionAdmin(BaseModelAdmin):
    list_display = ["customer", "transaction_type", "points", "sale", "staff", "created_at"]
    list_filter = ["transaction_type", "is_archived"]
    search_fields = ["customer__name", "customer__phone"]
    readonly_fields = ["created_at", "updated_at"]
