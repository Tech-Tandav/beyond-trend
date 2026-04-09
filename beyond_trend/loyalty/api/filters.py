import django_filters

from beyond_trend.loyalty.models import Customer, LoyaltyTransaction


class CustomerFilter(django_filters.FilterSet):
    phone = django_filters.CharFilter(field_name="phone", lookup_expr="icontains")

    class Meta:
        model = Customer
        fields = ["phone"]


class LoyaltyTransactionFilter(django_filters.FilterSet):
    customer = django_filters.UUIDFilter(field_name="customer__id")
    transaction_type = django_filters.CharFilter(field_name="transaction_type")
    date_from = django_filters.DateFilter(field_name="created_at__date", lookup_expr="gte")
    date_to = django_filters.DateFilter(field_name="created_at__date", lookup_expr="lte")

    class Meta:
        model = LoyaltyTransaction
        fields = ["customer", "transaction_type", "date_from", "date_to"]
