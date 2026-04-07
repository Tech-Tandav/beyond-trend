from django.db.models import F, Sum, Value
from django.db.models.functions import Coalesce

from rest_framework import generics, status
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from beyond_trend.core.pagination import CustomPagination
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


class ProductListView(generics.ListAPIView):
    serializer_class = ProductSerializer
    queryset = Product.objects.select_related("brand").all()
    permission_classes = [AllowAny]
    filterset_class = ProductFilter
    search_fields = ["model", "description", "brand__name", "barcode", "size", "color"]
    ordering_fields = ["model", "created_at", "size", "color"]


class ProductCreateView(generics.CreateAPIView):
    serializer_class = ProductSerializer
    queryset = Product.objects.select_related("brand").all()
    permission_classes = [IsAuthenticated]


class ProductRetrieveView(generics.RetrieveAPIView):
    serializer_class = ProductSerializer
    queryset = Product.objects.select_related("brand").all()
    permission_classes = [AllowAny]


class ProductUpdateView(generics.UpdateAPIView):
    serializer_class = ProductSerializer
    queryset = Product.objects.select_related("brand").all()
    permission_classes = [IsAuthenticated]


class ProductDestroyView(generics.DestroyAPIView):
    serializer_class = ProductSerializer
    queryset = Product.objects.select_related("brand").all()
    permission_classes = [IsAuthenticated]


class ProductCheckInView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
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


class ProductCheckOutView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
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
        qs = self.get_queryset().filter(
            quantity__gt=0,
            quantity__lte=F("variant__product__low_stock_threshold"),
        )
        serializer = self.get_serializer(qs, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=["get"], url_path="out-of-stock")
    def out_of_stock(self, request):
        """Return all out-of-stock variants."""
        qs = self.get_queryset().filter(quantity=0)
        serializer = self.get_serializer(qs, many=True)
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
    pagination_class = CustomPagination

    def get(self, request):
        from django.contrib.postgres.aggregates import ArrayAgg

        rows = (
            Product.objects.filter(is_published=True)
            .values("model", brand_name=Coalesce("brand__name", Value("")))
            .annotate(
                colors=ArrayAgg("color", distinct=True, ordering="color"),
                sizes=ArrayAgg("size", distinct=True, ordering="size"),
                quantity=Coalesce(Sum("stock__quantity"), 0),
            )
            .order_by("brand_name", "model")
        )

        paginator = self.pagination_class()
        page = paginator.paginate_queryset(rows, request, view=self)

        result = [
            {
                "slug": row['slug'],
                "brand_name": row["brand_name"],
                "model": row["model"],
                "color": row["colors"],
                "size": row["sizes"],
                "quantity": row["quantity"],
                "image": row["img"] if "img" in row else None,
            }
            for row in page
        ]

        return paginator.get_paginated_response(result)