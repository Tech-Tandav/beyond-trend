from django.db import models
from rest_framework import serializers

from beyond_trend.core.serializers import BaseModelSerializer

from beyond_trend.loyalty.models import Customer, LoyaltySettings, LoyaltyTransaction


class CustomerSerializer(BaseModelSerializer):
    points_value_npr = serializers.SerializerMethodField()
    transaction_count = serializers.SerializerMethodField()
    transaction_amount = serializers.SerializerMethodField()

    class Meta(BaseModelSerializer.Meta):
        model = Customer
        fields = [
            "id",
            "name",
            "email",
            "phone",
            "total_points",
            "points_value_npr",
            "is_redeemable",
            "transaction_count",
            "transaction_amount",
            "is_archived",
            "created_at",
        ]
        read_only_fields = [
            "id",
            "total_points",
            "points_value_npr",
            "is_redeemable",
            "transaction_count",
            "transaction_amount",
            "created_at",
        ]

    def get_transaction_count(self, obj):
        value = getattr(obj, "transaction_count", None)
        if value is None:
            value = obj.sales.count()
        return value

    def get_transaction_amount(self, obj):
        value = getattr(obj, "transaction_amount", None)
        if value is None:
            value = obj.sales.aggregate(total=models.Sum("total_amount"))["total"]
        return str(value or 0)

    def get_points_value_npr(self, obj):
        if not hasattr(self, "_point_value_npr"):
            settings = LoyaltySettings.objects.first()
            self._point_value_npr = settings.point_value_npr if settings else 0
        return str(obj.total_points * self._point_value_npr)


class LoyaltyTransactionSerializer(BaseModelSerializer):
    class Meta(BaseModelSerializer.Meta):
        model = LoyaltyTransaction
        fields = ["id", "customer", "points", "type", "sale", "notes", "created_at"]
        read_only_fields = ["id", "created_at"]


class LoyaltySettingsSerializer(BaseModelSerializer):
    class Meta(BaseModelSerializer.Meta):
        model = LoyaltySettings
        fields = ["id", "points_per_100_npr", "point_value_npr", "updated_at"]
        read_only_fields = ["id", "updated_at"]


class RedeemPointsSerializer(serializers.Serializer):
    customer_id = serializers.UUIDField()
    points = serializers.IntegerField(min_value=1)
    notes = serializers.CharField(required=False, allow_blank=True, default="")
