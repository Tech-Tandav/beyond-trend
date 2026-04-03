from rest_framework import serializers

from beyond_trend.core.serializers import BaseModelSerializer

from beyond_trend.inventory.models import Brand, Category, InventoryLog, Product, ProductVariant, Stock, ShoeProduct


class BrandSerializer(BaseModelSerializer):
    class Meta(BaseModelSerializer.Meta):
        model = Brand
        fields = ["id", "name", "slug", "is_archived", "created_at"]
        read_only_fields = ["id", "slug", "created_at"]


class CategorySerializer(BaseModelSerializer):
    class Meta(BaseModelSerializer.Meta):
        model = Category
        fields = ["id", "name", "slug", "is_archived", "created_at"]
        read_only_fields = ["id", "slug", "created_at"]


class ProductVariantSerializer(BaseModelSerializer):
    class Meta(BaseModelSerializer.Meta):
        model = ProductVariant
        fields = [
            "id",
            "product",
            "size",
            "color",
            "barcode",
            "cost_price",
            "selling_price",
            "low_stock_threshold",
            "is_archived",
            "created_at",
        ]
        read_only_fields = ["id", "barcode", "created_at"]


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
        fields = [
            "id",
            "name",
            "slug",
            "brand",
            "category",
            "description",
            "image",
            "is_published",
            "is_archived",
            "created_at",
        ]
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


class ShoeSerializer(BaseModelSerializer):
    class Meta(BaseModelSerializer.Meta):
        model = ShoeProduct
        fields = [
            "id",
            "name",
            "slug",
            "brand_name",
            "description",
            "image",
            "is_published",
            "is_archived",
            "created_at",
        ]
        read_only_fields = ["id", "slug", "created_at"]