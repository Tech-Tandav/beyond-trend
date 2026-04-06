from collections import defaultdict

from django.db.models import Sum

from rest_framework import status
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from beyond_trend.core.viewsets import BaseModelViewSet

from beyond_trend.inventory.models import Vendor, Brand, InventoryLog, Product, Stock
from beyond_trend.inventory.api.filters import InventoryLogFilter, ProductFilter, StockFilter
from beyond_trend.inventory.api.serializers import (
    VendorSerializer,
    BrandSerializer,
    CheckInSerializer,
    CheckOutSerializer,
    InventoryLogSerializer,
    ProductSerializer,
    StockSerializer,
)
from beyond_trend.inventory.api.usecases import CheckInUseCase, CheckOutUseCase


class VendorViewSet(BaseModelViewSet):
    serializer_class = VendorSerializer
    queryset = Vendor.objects.all()
    permission_classes = [IsAuthenticated]
    search_fields = ["name"]
    ordering_fields = ["name"]

class BrandViewSet(BaseModelViewSet):
    serializer_class = BrandSerializer
    queryset = Brand.objects.all()
    permission_classes = [IsAuthenticated]
    search_fields = ["name"]
    ordering_fields = ["name"]


class ProductViewSet(BaseModelViewSet):
    serializer_class = ProductSerializer
    queryset = Product.objects.select_related("brand").all()
    permission_classes = [IsAuthenticated]
    filterset_class = ProductFilter
    search_fields = ["model", "description", "brand__name", "barcode", "size", "color"]
    ordering_fields = ["model", "created_at", "size", "color"]

    @action(detail=False, methods=["post"], url_path="check-in")
    def check_in(self, request):
        """Add stock for a variant (Check-In)."""
        serializer = CheckInSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        use_case = CheckInUseCase(
            product_id=data["product_id"],
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
    search_fields = ["notes"]
    ordering_fields = ["created_at", "action", "quantity"]


class PublicInventoryView(APIView):
    """
    GET /api/v1/inventory/public/

    Public endpoint returning accumulated inventory grouped by brand + model.
    """

    permission_classes = [AllowAny]

    def get(self, request):
        products = (
            Product.objects.filter(is_published=True)
            .select_related("brand", "stock")
            .order_by("brand__name", "model")
        )

        grouped = defaultdict(lambda: {"colors": set(), "sizes": set(), "quantity": 0})

        for product in products:
            key = (product.brand.name if product.brand else "", product.model)
            grouped[key]["colors"].add(product.color)
            grouped[key]["sizes"].add(product.size)
            stock = getattr(product, "stock", None)
            if stock:
                grouped[key]["quantity"] += stock.quantity

        result = [
            {
                "brand_name": brand_name,
                "model": model,
                "color": sorted(data["colors"]),
                "size": sorted(data["sizes"]),
                "quantity": data["quantity"],
            }
            for (brand_name, model), data in grouped.items()
        ]

        return Response(result)