from rest_framework import serializers

from beyond_trend.core.serializers import BaseModelSerializer

from beyond_trend.inventory.models import (
    Brand,
    Category,
    InventoryLog,
    Product,
    ProductImage,
    SubCategory,
    Vendor,
)


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


class SubCategorySerializer(BaseModelSerializer):
    class Meta(BaseModelSerializer.Meta):
        model = SubCategory
        fields = [
            "id",
            "category",
            "name",
            "slug",
            "description",
            "is_active",
            "is_archived",
            "created_at",
        ]
        read_only_fields = ["id", "slug", "created_at"]


class CategorySerializer(BaseModelSerializer):
    subcategories = SubCategorySerializer(many=True, read_only=True)

    class Meta(BaseModelSerializer.Meta):
        model = Category
        fields = [
            "id",
            "name",
            "slug",
            "description",
            "is_active",
            "is_archived",
            "created_at",
            "subcategories",
        ]
        read_only_fields = ["id", "slug", "created_at"]


class ProductImageSerializer(BaseModelSerializer):
    class Meta(BaseModelSerializer.Meta):
        model = ProductImage
        fields = ["id", "product", "image", "is_primary", "order", "created_at"]
        read_only_fields = ["id", "created_at"]


class ProductSerializer(BaseModelSerializer):
    selling_price = serializers.DecimalField(
        max_digits=10, decimal_places=2, required=False, allow_null=True
    )
    is_low_stock = serializers.BooleanField(read_only=True)
    is_out_of_stock = serializers.BooleanField(read_only=True)
    images = ProductImageSerializer(many=True, read_only=True)
    uploaded_images = serializers.ListField(
        child=serializers.ImageField(),
        write_only=True,
        required=False,
    )

    class Meta(BaseModelSerializer.Meta):
        model = Product
        fields = [
            "id",
            "slug",
            "is_archived",
            "created_at",
            "brand",
            "category",
            "subcategory",
            "model",
            "vendor",
            "description",
            "images",
            "uploaded_images",
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

    def create(self, validated_data):
        uploaded_images = validated_data.pop("uploaded_images", [])
        product = super().create(validated_data)
        for index, image in enumerate(uploaded_images):
            ProductImage.objects.create(
                product=product,
                image=image,
                is_primary=(index == 0),
                order=index,
            )
        return product

    def update(self, instance, validated_data):
        uploaded_images = validated_data.pop("uploaded_images", None)
        product = super().update(instance, validated_data)
        if uploaded_images:
            existing_count = product.images.count()
            for index, image in enumerate(uploaded_images):
                ProductImage.objects.create(
                    product=product,
                    image=image,
                    is_primary=(existing_count == 0 and index == 0),
                    order=existing_count + index,
                )
        return product


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