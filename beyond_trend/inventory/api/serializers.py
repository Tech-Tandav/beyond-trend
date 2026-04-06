from rest_framework import serializers

from beyond_trend.core.serializers import BaseModelSerializer

from beyond_trend.inventory.models import Brand,  InventoryLog, Product, Stock, Vendor


class VendorSerializer(BaseModelSerializer):
    class Meta(BaseModelSerializer.Meta):
        model = Vendor
        fields = ["id", "name", "slug", "is_archived", "created_at", "contact_info", "pan_number", "vat_number"]
        read_only_fields = ["id", "slug", "created_at"]
        
        
        
class BrandSerializer(BaseModelSerializer):
    class Meta(BaseModelSerializer.Meta):
        model = Brand
        fields = ["id", "name", "slug", "is_archived", "created_at"]
        read_only_fields = ["id", "slug", "created_at"]


class StockSerializer(BaseModelSerializer):
    is_low_stock = serializers.BooleanField(read_only=True)
    is_out_of_stock = serializers.BooleanField(read_only=True)

    class Meta(BaseModelSerializer.Meta):
        model = Stock
        fields = ["id", "variant", "quantity", "is_low_stock", "is_out_of_stock", "updated_at"]
        read_only_fields = ["id", "is_low_stock", "is_out_of_stock", "updated_at"]


class ProductSerializer(BaseModelSerializer):
    class Meta(BaseModelSerializer.Meta):
        model = Product
        fields = '__all__'
        read_only_fields = ["id", "slug", "created_at"]


class InventoryLogSerializer(BaseModelSerializer):
    class Meta(BaseModelSerializer.Meta):
        model = InventoryLog
        fields = [
            "id",
            "variant",
            "action",
            "quantity",
            "staff",
            "notes",
            "created_at",
        ]
        read_only_fields = ["id", "staff", "created_at"]


class CheckInSerializer(serializers.Serializer):
    """Used for stock check-in (adding stock to an existing variant)."""
    variant_id = serializers.UUIDField()
    quantity = serializers.IntegerField(min_value=1)
    notes = serializers.CharField(required=False, allow_blank=True, default="")


class CheckOutSerializer(serializers.Serializer):
    """Used for single-variant stock check-out (manual inventory removal)."""
    variant_id = serializers.UUIDField()
    quantity = serializers.IntegerField(min_value=1)
    notes = serializers.CharField(required=False, allow_blank=True, default="")