import django_filters

from beyond_trend.inventory.models import InventoryLog, Product


class ProductFilter(django_filters.FilterSet):
    brand = django_filters.CharFilter(field_name="brand__slug")
    brand_name = django_filters.CharFilter(field_name="brand__name", lookup_expr="icontains")
    category = django_filters.CharFilter(field_name="category__slug")
    category_name = django_filters.CharFilter(field_name="category__name", lookup_expr="icontains")
    subcategory = django_filters.CharFilter(field_name="subcategory__slug")
    subcategory_name = django_filters.CharFilter(field_name="subcategory__name", lookup_expr="icontains")
    model = django_filters.CharFilter(lookup_expr="icontains")
    is_published = django_filters.BooleanFilter()
    is_featured = django_filters.BooleanFilter()
    show_in_website = django_filters.BooleanFilter()
    barcode = django_filters.CharFilter(lookup_expr="iexact")
    size = django_filters.CharFilter(lookup_expr="iexact")
    color = django_filters.CharFilter(lookup_expr="icontains")

    class Meta:
        model = Product
        fields = [
            "brand",
            "brand_name",
            "category",
            "category_name",
            "subcategory",
            "subcategory_name",
            "model",
            "is_published",
            "is_featured",
            "show_in_website",
            "barcode",
            "size",
            "color",
        ]



class InventoryLogFilter(django_filters.FilterSet):
    variant = django_filters.UUIDFilter(field_name="variant__id")
    action = django_filters.ChoiceFilter(choices=InventoryLog.ACTION_CHOICES)
    staff = django_filters.UUIDFilter(field_name="staff__id")
    date_from = django_filters.DateFilter(field_name="created_at__date", lookup_expr="gte")
    date_to = django_filters.DateFilter(field_name="created_at__date", lookup_expr="lte")

    class Meta:
        model = InventoryLog
        fields = ["variant", "action", "staff", "date_from", "date_to"]