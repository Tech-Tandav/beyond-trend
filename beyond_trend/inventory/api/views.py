from rest_framework import status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from beyond_trend.core.viewsets import BaseModelViewSet

from beyond_trend.inventory.models import Brand, Category, InventoryLog, Product, ProductVariant, Stock, ShoeProduct
from beyond_trend.inventory.api.filters import InventoryLogFilter, ProductFilter, ProductVariantFilter, StockFilter, ShoeFilter
from beyond_trend.inventory.api.serializers import (
    BrandSerializer,
    CategorySerializer,
    CheckInSerializer,
    CheckOutSerializer,
    InventoryLogSerializer,
    ProductSerializer,
    ProductVariantSerializer,
    StockSerializer,
    ShoeSerializer
)
from beyond_trend.inventory.api.usecases import CheckInUseCase, CheckOutUseCase


class BrandViewSet(BaseModelViewSet):
    serializer_class = BrandSerializer
    queryset = Brand.objects.all()
    permission_classes = [IsAuthenticated]
    search_fields = ["name"]
    ordering_fields = ["name"]


class CategoryViewSet(BaseModelViewSet):
    serializer_class = CategorySerializer
    queryset = Category.objects.all()
    permission_classes = [IsAuthenticated]
    search_fields = ["name"]
    ordering_fields = ["name"]


class ProductViewSet(BaseModelViewSet):
    serializer_class = ProductSerializer
    queryset = Product.objects.select_related("brand", "category").all()
    permission_classes = [IsAuthenticated]
    filterset_class = ProductFilter
    search_fields = ["name", "description", "brand__name", "category__name"]
    ordering_fields = ["name", "created_at"]


class ProductVariantViewSet(BaseModelViewSet):
    serializer_class = ProductVariantSerializer
    queryset = ProductVariant.objects.select_related("product").all()
    permission_classes = [IsAuthenticated]
    filterset_class = ProductVariantFilter
    search_fields = ["barcode", "size", "color", "product__name"]
    ordering_fields = ["size", "color", "selling_price", "cost_price"]

    @action(detail=False, methods=["post"], url_path="check-in")
    def check_in(self, request):
        """Add stock for a variant (Check-In)."""
        serializer = CheckInSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        use_case = CheckInUseCase(
            variant_id=data["variant_id"],
            quantity=data["quantity"],
            notes=data.get("notes", ""),
            staff=request.user,
        )
        return Response(use_case.execute(), status=status.HTTP_200_OK)

    @action(detail=False, methods=["post"], url_path="check-out")
    def check_out(self, request):
        """Remove stock for a variant (manual inventory check-out)."""
        serializer = CheckOutSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        use_case = CheckOutUseCase(
            variant_id=data["variant_id"],
            quantity=data["quantity"],
            notes=data.get("notes", ""),
            staff=request.user,
        )
        return Response(use_case.execute(), status=status.HTTP_200_OK)


class StockViewSet(BaseModelViewSet):
    serializer_class = StockSerializer
    queryset = Stock.objects.select_related("variant__product").all()
    permission_classes = [IsAuthenticated]
    http_method_names = ["get", "patch", "head", "options"]
    filterset_class = StockFilter
    ordering_fields = ["quantity", "variant__product__name"]

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
    http_method_names = ["get", "head", "options"]
    filterset_class = InventoryLogFilter
    search_fields = ["notes", "variant__product__name"]
    ordering_fields = ["created_at", "action", "quantity"]


class ShoeProductViewSet(BaseModelViewSet):
    serializer_class = ShoeSerializer
    queryset = ShoeProduct.objects.all()
    permission_classes = [IsAuthenticated]
    filterset_class = ShoeFilter
    lookup_field = "barcode"
    search_fields = ["brand_name", "description", "color", "size", "barcode"]
    ordering_fields = ["brand_name", "selling_price", "created_at"]