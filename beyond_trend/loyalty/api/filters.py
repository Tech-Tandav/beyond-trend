import django_filters

from beyond_trend.loyalty.models import Customer, LoyaltyTransaction


class CustomerFilter(django_filters.FilterSet):
    class Meta:
        model = Customer
        fields = {
            "email": ["exact", "icontains"],
            "phone": ["exact", "icontains"],
        }


class LoyaltyTransactionFilter(django_filters.FilterSet):
    customer = django_filters.UUIDFilter(field_name="customer__id")
    type = django_filters.ChoiceFilter(choices=LoyaltyTransaction.TYPE_CHOICES)
    date_from = django_filters.DateFilter(field_name="created_at__date", lookup_expr="gte")
    date_to = django_filters.DateFilter(field_name="created_at__date", lookup_expr="lte")

    class Meta:
        model = LoyaltyTransaction
        fields = ["customer", "type", "date_from", "date_to"]
