from rest_framework import serializers

from beyond_trend.core.serializers import BaseModelSerializer

from beyond_trend.inventory.models import Brand, InventoryLog, Product, Vendor


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


class ProductSerializer(BaseModelSerializer):
    selling_price = serializers.DecimalField(
        max_digits=10, decimal_places=2, required=False, allow_null=True
    )
    is_low_stock = serializers.BooleanField(read_only=True)
    is_out_of_stock = serializers.BooleanField(read_only=True)

    class Meta(BaseModelSerializer.Meta):
        model = Product
        fields = [
            "id",
            "slug",
            "is_archived",
            "created_at",
            "brand",
            "model",
            "vendor",
            "description",
            "image",
            "size",
            "color",
            "barcode",
            "selling_price",
            "quantity",
            "low_stock_threshold",
            "is_low_stock",
            "is_out_of_stock",
        ]
        read_only_fields = ["id", "slug", "created_at", "is_low_stock", "is_out_of_stock"]


class InventoryLogSerializer(BaseModelSerializer):
    class Meta(BaseModelSerializer.Meta):
        model = InventoryLog
        fields = [
            "id",
            "product",
            "action",
            "quantity",
            "staff",
            "notes",
            "created_at",
        ]
        read_only_fields = ["id", "staff", "created_at"]


class CheckInSerializer(serializers.Serializer):
    """Used for stock check-in (adding stock to an existing product)."""
    product_id = serializers.UUIDField()
    quantity = serializers.IntegerField(min_value=1)
    notes = serializers.CharField(required=False, allow_blank=True, default="")


class CheckOutSerializer(serializers.Serializer):
    """Used for single-product stock check-out (manual inventory removal)."""
    product_id = serializers.UUIDField()
    quantity = serializers.IntegerField(min_value=1)
    notes = serializers.CharField(required=False, allow_blank=True, default="")