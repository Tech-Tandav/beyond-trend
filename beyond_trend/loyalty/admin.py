from django.contrib import admin

from beyond_trend.core.admin import BaseModelAdmin

from beyond_trend.loyalty.models import Customer, LoyaltySettings, LoyaltyTransaction


@admin.register(Customer)
class CustomerAdmin(BaseModelAdmin):
    list_display = ["name", "email", "phone", "total_points", "created_at"]
    search_fields = ["name", "email", "phone", "id"]
    readonly_fields = ["total_points", "created_at", "updated_at"]


@admin.register(LoyaltyTransaction)
class LoyaltyTransactionAdmin(BaseModelAdmin):
    list_display = ["customer", "type", "points", "sale", "created_at"]
    list_filter = ["type", "is_archived"]
    search_fields = ["customer__name", "customer__email", "id"]


@admin.register(LoyaltySettings)
class LoyaltySettingsAdmin(BaseModelAdmin):
    list_display = ["points_per_100_npr", "point_value_npr"]

    def has_add_permission(self, request):
        return not LoyaltySettings.objects.exists()

    def has_delete_permission(self, request, obj=None):
        return False
