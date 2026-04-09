from rest_framework import serializers

from beyond_trend.core.serializers import BaseModelSerializer
from beyond_trend.loyalty.models import Customer, LoyaltyTransaction


class CustomerSerializer(BaseModelSerializer):
    available_points = serializers.IntegerField(read_only=True)
    tier_discount = serializers.DecimalField(
        max_digits=5, decimal_places=2, read_only=True
    )

    class Meta(BaseModelSerializer.Meta):
        model = Customer
        fields = [
            "id",
            "name",
            "phone",
            "email",
            "address",
            "tier",
            "total_points",
            "redeemed_points",
            "available_points",
            "tier_discount",
            "total_spend",
            "created_at",
        ]
        read_only_fields = [
            "id",
            "tier",
            "total_points",
            "redeemed_points",
            "total_spend",
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
            "sale",
            "staff",
            "notes",
            "created_at",
        ]
        read_only_fields = ["id", "staff", "created_at"]


class EarnPointsSerializer(serializers.Serializer):
    customer_id = serializers.UUIDField()
    sale_id = serializers.UUIDField(required=False)
    amount = serializers.DecimalField(
        max_digits=12,
        decimal_places=2,
        help_text="Purchase amount in NPR to calculate points from.",
    )
    notes = serializers.CharField(required=False, allow_blank=True, default="")


class RedeemPointsSerializer(serializers.Serializer):
    customer_id = serializers.UUIDField()
    points = serializers.IntegerField(min_value=1)
    notes = serializers.CharField(required=False, allow_blank=True, default="")


class CustomerLookupSerializer(serializers.Serializer):
    phone = serializers.CharField(max_length=20)
