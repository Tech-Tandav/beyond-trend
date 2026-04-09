import django_filters

from beyond_trend.sales.models import Sale, Sale


class SaleFilter(django_filters.FilterSet):
    staff = django_filters.UUIDFilter(field_name="staff__id")
    date_from = django_filters.DateFilter(field_name="created_at__date", lookup_expr="gte")
    date_to = django_filters.DateFilter(field_name="created_at__date", lookup_expr="lte")

    class Meta:
        model = Sale
        fields = ["staff", "date_from", "date_to"]
