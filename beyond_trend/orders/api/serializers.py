from rest_framework import serializers

from beyond_trend.core.serializers import BaseModelSerializer
from beyond_trend.inventory.api.serializers import ProductSerializer

from beyond_trend.orders.models import Order, OrderItem, PreOrder


class OrderItemSerializer(BaseModelSerializer):
    total = serializers.DecimalField(max_digits=12, decimal_places=2, read_only=True)
    product = ProductSerializer(read_only=True)

    class Meta(BaseModelSerializer.Meta):
        model = OrderItem
        fields = ["id", "product", "quantity", "price", "total"]
        read_only_fields = ["id", "total", "product"]


class OrderSerializer(BaseModelSerializer):
    items = OrderItemSerializer(many=True, read_only=True)

    class Meta(BaseModelSerializer.Meta):
        model = Order
        fields = [
            "id",
            "customer_name",
            "email",
            "phone",
            "status",
            "total_amount",
            "notes",
            "loyalty_customer",
            "items",
            "is_archived",
            "created_at",
        ]
        read_only_fields = ["id", "total_amount", "created_at"]


class CreateOrderItemSerializer(serializers.Serializer):
    product_id = serializers.UUIDField()
    quantity = serializers.IntegerField(min_value=1)
    selling_price = serializers.DecimalField(
        max_digits=10, decimal_places=2, required=False, allow_null=True
    )


class CreateOrderSerializer(serializers.Serializer):
    customer_name = serializers.CharField(max_length=255)
    email = serializers.EmailField()
    phone = serializers.CharField(max_length=20, required=False, allow_blank=True, default="")
    items = CreateOrderItemSerializer(many=True)
    notes = serializers.CharField(required=False, allow_blank=True, default="")
    loyalty_customer_id = serializers.UUIDField(required=False, allow_null=True)

    def validate_items(self, value):
        if not value:
            raise serializers.ValidationError("At least one item is required.")
        return value


class PreOrderSerializer(BaseModelSerializer):
    class Meta(BaseModelSerializer.Meta):
        model = PreOrder
        fields = [
            "id",
            "customer_name",
            "email",
            "phone",
            "product_name",
            "brand",
            "size",
            "color",
            "notes",
            "status",
            "is_archived",
            "created_at",
        ]
        read_only_fields = ["id", "status", "created_at"]


class UpdateOrderStatusSerializer(serializers.Serializer):
    status = serializers.ChoiceField(choices=Order.STATUS_CHOICES)
