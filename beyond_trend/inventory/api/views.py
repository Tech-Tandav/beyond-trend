from django.db.models import F, Sum, Value
from django.db.models.functions import Coalesce

from drf_spectacular.utils import (
    OpenApiExample,
    OpenApiResponse,
    extend_schema,
    extend_schema_view,
    inline_serializer,
)
from rest_framework import generics, serializers, status
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


StockMovementResponseSerializer = inline_serializer(
    name="StockMovementResponse",
    fields={
        "detail": serializers.CharField(),
        "variant": serializers.CharField(),
        "new_quantity": serializers.IntegerField(),
    },
)


@extend_schema_view(
    list=extend_schema(
        tags=["Inventory - Vendors"],
        summary="List vendors",
        description="Returns a paginated list of vendors. Supports `?search=` by name and `?ordering=name`.",
    ),
    retrieve=extend_schema(tags=["Inventory - Vendors"], summary="Get a vendor"),
    create=extend_schema(tags=["Inventory - Vendors"], summary="Create a vendor"),
    update=extend_schema(tags=["Inventory - Vendors"], summary="Replace a vendor"),
    partial_update=extend_schema(tags=["Inventory - Vendors"], summary="Patch a vendor"),
    destroy=extend_schema(tags=["Inventory - Vendors"], summary="Archive a vendor"),
)
class VendorViewSet(BaseModelViewSet):
    serializer_class = VendorSerializer
    queryset = Vendor.objects.all()
    permission_classes = [IsAuthenticated]
    search_fields = ["name"]
    ordering_fields = ["name"]


@extend_schema_view(
    list=extend_schema(
        tags=["Inventory - Brands"],
        summary="List brands",
        description="Returns a paginated list of brands. Supports `?search=` by name.",
    ),
    retrieve=extend_schema(tags=["Inventory - Brands"], summary="Get a brand"),
    create=extend_schema(tags=["Inventory - Brands"], summary="Create a brand"),
    update=extend_schema(tags=["Inventory - Brands"], summary="Replace a brand"),
    partial_update=extend_schema(tags=["Inventory - Brands"], summary="Patch a brand"),
    destroy=extend_schema(tags=["Inventory - Brands"], summary="Archive a brand"),
)
class BrandViewSet(BaseModelViewSet):
    serializer_class = BrandSerializer
    queryset = Brand.objects.all()
    permission_classes = [IsAuthenticated]
    search_fields = ["name"]
    ordering_fields = ["name"]


@extend_schema(
    tags=["Inventory - Products"],
    summary="List products",
    description=(
        "Returns a paginated list of product variants. Each row represents a unique "
        "**brand + model + size + color** combination.\n\n"
        "Supports filtering via `ProductFilter`, full-text search on "
        "`model`, `description`, `brand__name`, `barcode`, `size`, `color`, and "
        "ordering by `model`, `created_at`, `size`, `color`."
    ),
)
class ProductListView(generics.ListAPIView):
    serializer_class = ProductSerializer
    queryset = Product.objects.select_related("brand").all()
    permission_classes = [AllowAny]
    filterset_class = ProductFilter
    search_fields = ["model", "description", "brand__name", "barcode", "size", "color"]
    ordering_fields = ["model", "created_at", "size", "color"]


@extend_schema(
    tags=["Inventory - Products"],
    summary="Create a product variant",
    description="Creates a new product variant. The `slug` field is auto-generated from brand + model + size + color.",
)
class ProductCreateView(generics.CreateAPIView):
    serializer_class = ProductSerializer
    queryset = Product.objects.select_related("brand").all()
    permission_classes = [IsAuthenticated]


@extend_schema(
    tags=["Inventory - Products"],
    summary="Get a product variant by slug",
)
class ProductRetrieveView(generics.RetrieveAPIView):
    serializer_class = ProductSerializer
    queryset = Product.objects.select_related("brand").all()
    permission_classes = [AllowAny]
    lookup_field = "barcode"


@extend_schema(
    tags=["Inventory - Products"],
    summary="Update a product variant",
)
class ProductUpdateView(generics.UpdateAPIView):
    serializer_class = ProductSerializer
    queryset = Product.objects.select_related("brand").all()
    permission_classes = [IsAuthenticated]
    lookup_field = "slug"


@extend_schema(
    tags=["Inventory - Products"],
    summary="Delete a product variant",
)
class ProductDestroyView(generics.DestroyAPIView):
    serializer_class = ProductSerializer
    queryset = Product.objects.select_related("brand").all()
    permission_classes = [IsAuthenticated]
    lookup_field = "slug"


@extend_schema(
    tags=["Inventory - Operations"],
    summary="Stock check-in",
    description=(
        "Increments the stock for a product variant and writes an `InventoryLog` "
        "entry of type `CHECK_IN`. Use this when receiving stock from a vendor."
    ),
    request=CheckInSerializer,
    responses={200: StockMovementResponseSerializer},
    examples=[
        OpenApiExample(
            "Check in 10 units",
            value={"variant_id": "0d3b3ce6-1b9f-4f1d-8f5d-6f1a2c2d3e4f", "quantity": 10, "notes": "Vendor delivery"},
            request_only=True,
        ),
        OpenApiExample(
            "Success response",
            value={"detail": "Stock checked in successfully.", "variant": "Nike AirMax 42 Black", "new_quantity": 25},
            response_only=True,
        ),
    ],
)
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


@extend_schema(
    tags=["Inventory - Operations"],
    summary="Stock check-out",
    description=(
        "Decrements the stock for a product variant and writes an `InventoryLog` "
        "entry of type `CHECK_OUT`. Use this for manual write-offs (damaged stock, "
        "returns to vendor, etc.)."
    ),
    request=CheckOutSerializer,
    responses={
        200: StockMovementResponseSerializer,
        400: OpenApiResponse(description="Insufficient stock or no stock record."),
        404: OpenApiResponse(description="Variant not found."),
    },
)
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


@extend_schema_view(
    list=extend_schema(
        tags=["Inventory - Stock"],
        summary="List stock levels",
        description="Returns the current stock quantity for every product variant.",
    ),
    retrieve=extend_schema(tags=["Inventory - Stock"], summary="Get stock for a variant"),
    partial_update=extend_schema(
        tags=["Inventory - Stock"],
        summary="Patch a stock row",
        description="Direct stock adjustment. Prefer the check-in / check-out endpoints when possible — they leave an audit trail.",
    ),
)
class StockViewSet(BaseModelViewSet):
    serializer_class = StockSerializer
    queryset = Stock.objects.select_related("variant__product").all()
    permission_classes = [IsAuthenticated]
    http_method_names = ["get", "patch", "head", "options"]
    filterset_class = StockFilter
    ordering_fields = ["quantity", "variant__product__name"]

    @extend_schema(
        tags=["Inventory - Stock"],
        summary="List low-stock variants",
        description="Returns variants whose `quantity` is greater than 0 but at or below their per-product `low_stock_threshold`.",
        responses={200: StockSerializer(many=True)},
    )
    @action(detail=False, methods=["get"], url_path="low-stock")
    def low_stock(self, request):
        """Return all variants with low stock."""
        qs = self.get_queryset().filter(
            quantity__gt=0,
            quantity__lte=F("variant__product__low_stock_threshold"),
        )
        serializer = self.get_serializer(qs, many=True)
        return Response(serializer.data)

    @extend_schema(
        tags=["Inventory - Stock"],
        summary="List out-of-stock variants",
        description="Returns variants whose `quantity` is exactly 0.",
        responses={200: StockSerializer(many=True)},
    )
    @action(detail=False, methods=["get"], url_path="out-of-stock")
    def out_of_stock(self, request):
        """Return all out-of-stock variants."""
        qs = self.get_queryset().filter(quantity=0)
        serializer = self.get_serializer(qs, many=True)
        return Response(serializer.data)


@extend_schema_view(
    list=extend_schema(
        tags=["Inventory - Logs"],
        summary="List inventory log entries",
        description="Read-only audit trail of every stock movement (check-ins, check-outs, sales).",
    ),
    retrieve=extend_schema(tags=["Inventory - Logs"], summary="Get a log entry"),
)
class InventoryLogViewSet(BaseModelViewSet):
    serializer_class = InventoryLogSerializer
    queryset = InventoryLog.objects.select_related("variant__product", "staff").all()
    permission_classes = [IsAuthenticated]
    http_method_names = ["get", "head", "options"]
    filterset_class = InventoryLogFilter
    search_fields = ["notes"]
    ordering_fields = ["created_at", "action", "quantity"]


class PublicInventoryItemSerializer(serializers.Serializer):
    slug = serializers.CharField()
    brand_name = serializers.CharField()
    model = serializers.CharField()
    color = serializers.ListField(child=serializers.CharField())
    size = serializers.ListField(child=serializers.CharField())
    barcode = serializers.ListField(child=serializers.CharField())
    quantity = serializers.IntegerField()
    image = serializers.CharField(allow_null=True)


@extend_schema(
    tags=["Inventory - Public"],
    summary="Public catalog (grouped by brand + model)",
    description=(
        "Public, unauthenticated endpoint. Aggregates published variants by `brand + model` "
        "and returns the available colors, sizes, and total quantity in stock. Used by the "
        "storefront to render product cards."
    ),
    responses={200: PublicInventoryItemSerializer(many=True)},
)
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
            .values("slug", "model", "image", brand_name=Coalesce("brand__name", Value("")))
            .annotate(
                colors=ArrayAgg("color", distinct=True, ordering="color"),
                sizes=ArrayAgg("size", distinct=True, ordering="size"),
                barcodes=ArrayAgg("barcode", distinct=True, ordering="barcode"),
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
                "barcode": row["barcodes"],
                "quantity": row["quantity"],
                "image": row["img"] if "img" in row else None,
            }
            for row in page
        ]

        return paginator.get_paginated_response(result)
