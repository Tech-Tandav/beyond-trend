from django.db import transaction
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from beyond_trend.core.viewsets import BaseModelViewSet

from ..models import Brand, Category, InventoryLog, Product, ProductVariant, Stock
from .serializers import (
    BrandSerializer,
    CategorySerializer,
    CheckInSerializer,
    CheckOutSerializer,
    InventoryLogSerializer,
    ProductSerializer,
    ProductVariantSerializer,
    StockSerializer,
)


class BrandViewSet(BaseModelViewSet):
    serializer_class = BrandSerializer
    queryset = Brand.objects.all()
    permission_classes = [IsAuthenticated]


class CategoryViewSet(BaseModelViewSet):
    serializer_class = CategorySerializer
    queryset = Category.objects.all()
    permission_classes = [IsAuthenticated]


class ProductViewSet(BaseModelViewSet):
    serializer_class = ProductSerializer
    queryset = Product.objects.select_related("brand", "category").all()
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        qs = super().get_queryset()
        brand = self.request.query_params.get("brand")
        category = self.request.query_params.get("category")
        if brand:
            qs = qs.filter(brand__slug=brand)
        if category:
            qs = qs.filter(category__slug=category)
        return qs


class ProductVariantViewSet(BaseModelViewSet):
    serializer_class = ProductVariantSerializer
    queryset = ProductVariant.objects.select_related("product").all()
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        qs = super().get_queryset()
        product_id = self.request.query_params.get("product")
        barcode = self.request.query_params.get("barcode")
        if product_id:
            qs = qs.filter(product__id=product_id)
        if barcode:
            qs = qs.filter(barcode=barcode)
        return qs

    @action(detail=False, methods=["post"], url_path="check-in")
    @transaction.atomic
    def check_in(self, request):
        """Add stock for a variant (Check-In)."""
        serializer = CheckInSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        variant_id = serializer.validated_data["variant_id"]
        quantity = serializer.validated_data["quantity"]
        notes = serializer.validated_data.get("notes", "")

        try:
            variant = ProductVariant.objects.get(id=variant_id)
        except ProductVariant.DoesNotExist:
            return Response(
                {"detail": "Variant not found."},
                status=status.HTTP_404_NOT_FOUND,
            )

        stock, _ = Stock.objects.get_or_create(variant=variant)
        stock.quantity += quantity
        stock.save(update_fields=["quantity"])

        InventoryLog.objects.create(
            variant=variant,
            action=InventoryLog.CHECK_IN,
            quantity=quantity,
            staff=request.user,
            notes=notes,
        )

        return Response(
            {
                "detail": "Stock checked in successfully.",
                "variant": str(variant),
                "new_quantity": stock.quantity,
            },
            status=status.HTTP_200_OK,
        )

    @action(detail=False, methods=["post"], url_path="check-out")
    @transaction.atomic
    def check_out(self, request):
        """Remove stock for a variant (manual inventory check-out)."""
        serializer = CheckOutSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        variant_id = serializer.validated_data["variant_id"]
        quantity = serializer.validated_data["quantity"]
        notes = serializer.validated_data.get("notes", "")

        try:
            variant = ProductVariant.objects.get(id=variant_id)
        except ProductVariant.DoesNotExist:
            return Response(
                {"detail": "Variant not found."},
                status=status.HTTP_404_NOT_FOUND,
            )

        try:
            stock = Stock.objects.get(variant=variant)
        except Stock.DoesNotExist:
            return Response(
                {"detail": "No stock record for this variant."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if stock.quantity < quantity:
            return Response(
                {"detail": f"Insufficient stock. Available: {stock.quantity}"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        stock.quantity -= quantity
        stock.save(update_fields=["quantity"])

        InventoryLog.objects.create(
            variant=variant,
            action=InventoryLog.CHECK_OUT,
            quantity=-quantity,
            staff=request.user,
            notes=notes,
        )

        return Response(
            {
                "detail": "Stock checked out successfully.",
                "variant": str(variant),
                "new_quantity": stock.quantity,
            },
            status=status.HTTP_200_OK,
        )


class StockViewSet(BaseModelViewSet):
    serializer_class = StockSerializer
    queryset = Stock.objects.select_related("variant__product").all()
    permission_classes = [IsAuthenticated]
    http_method_names = ["get", "patch", "head", "options"]  # no create/delete via API

    @action(detail=False, methods=["get"], url_path="low-stock")
    def low_stock(self, request):
        """Return all variants with low stock."""
        items = [s for s in self.get_queryset() if s.is_low_stock]
        serializer = self.get_serializer(items, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=["get"], url_path="out-of-stock")
    def out_of_stock(self, request):
        """Return all out-of-stock variants."""
        items = [s for s in self.get_queryset() if s.is_out_of_stock]
        serializer = self.get_serializer(items, many=True)
        return Response(serializer.data)


class InventoryLogViewSet(BaseModelViewSet):
    serializer_class = InventoryLogSerializer
    queryset = InventoryLog.objects.select_related("variant__product", "staff").all()
    permission_classes = [IsAuthenticated]
    http_method_names = ["get", "head", "options"]  # logs are read-only via API

    def get_queryset(self):
        qs = super().get_queryset()
        variant_id = self.request.query_params.get("variant")
        action_filter = self.request.query_params.get("action")
        if variant_id:
            qs = qs.filter(variant__id=variant_id)
        if action_filter:
            qs = qs.filter(action=action_filter)
        return qs
