from rest_framework import serializers

from beyond_trend.core.serializers import BaseModelSerializer

from ..models import Sale, SaleItem


class SaleItemSerializer(BaseModelSerializer):
    total = serializers.DecimalField(max_digits=12, decimal_places=2, read_only=True)

    class Meta(BaseModelSerializer.Meta):
        model = SaleItem
        fields = ["id", "variant", "quantity", "selling_price", "total"]
        read_only_fields = ["id", "total"]


class SaleSerializer(BaseModelSerializer):
    items = SaleItemSerializer(many=True, read_only=True)

    class Meta(BaseModelSerializer.Meta):
        model = Sale
        fields = [
            "id",
            "staff",
            "customer",
            "subtotal",
            "discount_amount",
            "total_amount",
            "loyalty_points_used",
            "loyalty_points_earned",
            "notes",
            "items",
            "created_at",
        ]
        read_only_fields = [
            "id",
            "staff",
            "subtotal",
            "total_amount",
            "loyalty_points_earned",
            "created_at",
        ]


class CheckoutItemSerializer(serializers.Serializer):
    variant_id = serializers.UUIDField()
    quantity = serializers.IntegerField(min_value=1)
    selling_price = serializers.DecimalField(max_digits=10, decimal_places=2)


class CheckoutSerializer(serializers.Serializer):
    """Full POS checkout — creates a Sale with items, reduces stock, awards loyalty points."""
    items = CheckoutItemSerializer(many=True)
    customer_id = serializers.UUIDField(required=False, allow_null=True)
    loyalty_points_used = serializers.IntegerField(min_value=0, default=0)
    notes = serializers.CharField(required=False, allow_blank=True, default="")

    def validate_items(self, value):
        if not value:
            raise serializers.ValidationError("At least one item is required.")
        return value
