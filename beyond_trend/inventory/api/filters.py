import django_filters

from beyond_trend.inventory.models import InventoryLog, Product, Stock


class ProductFilter(django_filters.FilterSet):
    brand = django_filters.CharFilter(field_name="brand__slug")
    model = django_filters.CharFilter(lookup_expr="icontains")
    is_published = django_filters.BooleanFilter()
    barcode = django_filters.CharFilter(lookup_expr="iexact")
    size = django_filters.CharFilter(lookup_expr="iexact")
    color = django_filters.CharFilter(lookup_expr="icontains")

    class Meta:
        model = Product
        fields = ["brand", "model", "is_published", "barcode", "size", "color"]



class StockFilter(django_filters.FilterSet):
    product = django_filters.UUIDFilter(field_name="product__id")
    brand = django_filters.CharFilter(field_name="product__brand__slug")

    class Meta:
        model = Stock
        fields = ["product", "brand"]


class InventoryLogFilter(django_filters.FilterSet):
    variant = django_filters.UUIDFilter(field_name="variant__id")
    action = django_filters.ChoiceFilter(choices=InventoryLog.ACTION_CHOICES)
    staff = django_filters.UUIDFilter(field_name="staff__id")
    date_from = django_filters.DateFilter(field_name="created_at__date", lookup_expr="gte")
    date_to = django_filters.DateFilter(field_name="created_at__date", lookup_expr="lte")

    class Meta:
        model = InventoryLog
        fields = ["variant", "action", "staff", "date_from", "date_to"]