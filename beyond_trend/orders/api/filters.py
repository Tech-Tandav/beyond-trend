import django_filters

from beyond_trend.orders.models import Order, PreOrder


class OrderFilter(django_filters.FilterSet):
    status = django_filters.ChoiceFilter(choices=Order.STATUS_CHOICES)
    loyalty_customer = django_filters.UUIDFilter(field_name="loyalty_customer__id")
    date_from = django_filters.DateFilter(field_name="created_at__date", lookup_expr="gte")
    date_to = django_filters.DateFilter(field_name="created_at__date", lookup_expr="lte")

    class Meta:
        model = Order
        fields = ["status", "loyalty_customer", "date_from", "date_to"]


class PreOrderFilter(django_filters.FilterSet):
    status = django_filters.ChoiceFilter(choices=PreOrder.STATUS_CHOICES)

    class Meta:
        model = PreOrder
        fields = ["status"]
