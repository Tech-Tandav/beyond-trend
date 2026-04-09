from rest_framework import serializers

from beyond_trend.core.serializers import BaseModelSerializer
from beyond_trend.loyalty.models import Customer, LoyaltyTransaction


class CustomerSerializer(BaseModelSerializer):
    is_discount_eligible = serializers.BooleanField(read_only=True)

    class Meta(BaseModelSerializer.Meta):
        model = Customer
        fields = [
            "id",
            "name",
            "phone",
            "email",
            "address",
            "total_points",
            "is_discount_eligible",
            "created_at",
        ]
        read_only_fields = [
            "id",
            "total_points",
            "created_at",
        ]


class LoyaltyTransactionSerializer(BaseModelSerializer):
    class Meta(BaseModelSerializer.Meta):
        model = LoyaltyTransaction
        fields = [
            "id",
            "customer",
            "transaction_type",
            "points",
            "discount_applied",
            "sale",
            "staff",
            "notes",
            "created_at",
        ]
        read_only_fields = ["id", "staff", "created_at"]


class EarnPointsSerializer(serializers.Serializer):
    customer_id = serializers.UUIDField()
    sale_id = serializers.UUIDField(required=False)
    notes = serializers.CharField(required=False, allow_blank=True, default="")


class CustomerLookupSerializer(serializers.Serializer):
    phone = serializers.CharField(max_length=20)
