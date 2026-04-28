from rest_framework import serializers

from beyond_trend.core.serializers import BaseModelSerializer
from beyond_trend.inventory.api.serializers import ProductSerializer
from beyond_trend.inventory.models import Product

from ..models import Sale, SaleItem


class SaleItemSerializer(BaseModelSerializer):
    product = ProductSerializer(read_only=True)
    product_id = serializers.PrimaryKeyRelatedField(
        queryset=Product.objects.all(),
        source="product",
        write_only=True,
    )
    total = serializers.DecimalField(max_digits=12, decimal_places=2, read_only=True)

    class Meta(BaseModelSerializer.Meta):
        model = SaleItem
        fields = ["id", "product", "product_id", "quantity", "selling_price", "total"]
        read_only_fields = ["id", "total"]


class SaleSerializer(BaseModelSerializer):
    items = SaleItemSerializer(many=True, read_only=True)

    class Meta(BaseModelSerializer.Meta):
        model = Sale
        fields = [
            "id",
            "staff",
            "subtotal",
            "discount_amount",
            "total_amount",
            "notes",
            "items",
            "created_at",
        ]
        read_only_fields = [
            "id",
            "staff",
            "subtotal",
            "total_amount",
            "created_at",
        ]


class CheckoutItemSerializer(serializers.Serializer):
    product_id = serializers.UUIDField()
    quantity = serializers.IntegerField(min_value=1, required=False)
    selling_price = serializers.DecimalField(max_digits=10, decimal_places=2, required=False)


class CheckoutSerializer(serializers.Serializer):
    """Full POS checkout — creates a Sale with items and reduces stock.

    When `order_id` is provided, `items` is treated as per-product selling-price
    overrides (quantity is taken from the order). For direct checkouts, `items`
    must include quantity.
    """
    items = CheckoutItemSerializer(many=True, required=False)
    order_id = serializers.UUIDField(required=False, allow_null=True)
    notes = serializers.CharField(required=False, allow_blank=True, default="")

    def validate(self, attrs):
        if not attrs.get("order_id") and not attrs.get("items"):
            raise serializers.ValidationError(
                "Provide either `order_id` or `items`."
            )
        if not attrs.get("order_id"):
            for item in attrs.get("items") or []:
                if "quantity" not in item:
                    raise serializers.ValidationError(
                        "`quantity` is required for direct checkout items."
                    )
        return attrs


class ShoeCheckoutSerializer(serializers.Serializer):
    quantity = serializers.IntegerField(min_value=1)
    selling_price = serializers.DecimalField(max_digits=10, decimal_places=2)
    bar_code = serializers.CharField(max_length=255)
    phone_number = serializers.CharField(max_length=20, required=False, allow_blank=True, default="")