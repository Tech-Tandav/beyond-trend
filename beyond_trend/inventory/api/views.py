from django.db.models import Sum, Value
from django.db.models.functions import Coalesce

from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import (
    OpenApiExample,
    OpenApiParameter,
    OpenApiResponse,
    extend_schema,
    extend_schema_view,
    inline_serializer,
)
from rest_framework import generics, serializers, status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from beyond_trend.core.excel import ExcelExportAPIView
from beyond_trend.core.pagination import CustomPagination
from beyond_trend.core.viewsets import BaseModelViewSet

from beyond_trend.inventory.models import Vendor, Brand, InventoryLog, Product
from beyond_trend.inventory.api.filters import InventoryLogFilter, ProductFilter
from beyond_trend.inventory.api.serializers import (
    VendorSerializer,
    BrandSerializer,
    CheckInSerializer,
    CheckOutSerializer,
    InventoryLogSerializer,
    ProductSerializer,
)
from beyond_trend.inventory.api.usecases import CheckInUseCase, CheckOutUseCase


StockMovementResponseSerializer = inline_serializer(
    name="StockMovementResponse",
    fields={
        "detail": serializers.CharField(),
        "product": serializers.CharField(),
        "new_quantity": serializers.IntegerField(),
    },
)


@extend_schema_view(
    list=extend_schema(
        tags=["Inventory - Vendors"],
        summary="List vendors",
        description="Returns a paginated list of vendors. Supports `?search=` by name and `?ordering=name`.",
        parameters=[
            OpenApiParameter("search", OpenApiTypes.STR, OpenApiParameter.QUERY, description="Search by vendor name."),
            OpenApiParameter("ordering", OpenApiTypes.STR, OpenApiParameter.QUERY, description="Order by: name (prefix `-` for descending)."),
        ],
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
        parameters=[
            OpenApiParameter("search", OpenApiTypes.STR, OpenApiParameter.QUERY, description="Search by brand name."),
            OpenApiParameter("ordering", OpenApiTypes.STR, OpenApiParameter.QUERY, description="Order by: name (prefix `-` for descending)."),
        ],
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
    parameters=[
        OpenApiParameter("brand", OpenApiTypes.STR, OpenApiParameter.QUERY, description="Filter by brand slug (exact match)."),
        OpenApiParameter("model", OpenApiTypes.STR, OpenApiParameter.QUERY, description="Filter by model name (case-insensitive contains)."),
        OpenApiParameter("is_published", OpenApiTypes.BOOL, OpenApiParameter.QUERY, description="Filter by published flag."),
        OpenApiParameter("barcode", OpenApiTypes.STR, OpenApiParameter.QUERY, description="Filter by barcode (case-insensitive exact)."),
        OpenApiParameter("size", OpenApiTypes.STR, OpenApiParameter.QUERY, description="Filter by size (case-insensitive exact)."),
        OpenApiParameter("color", OpenApiTypes.STR, OpenApiParameter.QUERY, description="Filter by color (case-insensitive contains)."),
        OpenApiParameter("search", OpenApiTypes.STR, OpenApiParameter.QUERY, description="Free-text search across model, description, brand name, barcode, size, color."),
        OpenApiParameter("ordering", OpenApiTypes.STR, OpenApiParameter.QUERY, description="Order by: model, created_at, size, color (prefix `-` for descending)."),
    ],
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
            value={"product_id": "0d3b3ce6-1b9f-4f1d-8f5d-6f1a2c2d3e4f", "quantity": 10, "notes": "Vendor delivery"},
            request_only=True,
        ),
        OpenApiExample(
            "Success response",
            value={"detail": "Stock checked in successfully.", "product": "Nike AirMax 42 Black", "new_quantity": 25},
            response_only=True,
        ),
    ],
)
class ProductCheckInView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        """Add stock for a product (Check-In)."""
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
        400: OpenApiResponse(description="Insufficient stock."),
        404: OpenApiResponse(description="Product not found."),
    },
)
class ProductCheckOutView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        """Remove stock for a product (manual inventory check-out)."""
        serializer = CheckOutSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        use_case = CheckOutUseCase(
            product_id=data["product_id"],
            quantity=data["quantity"],
            notes=data.get("notes", ""),
            staff=request.user,
        )
        return Response(use_case.execute(), status=status.HTTP_200_OK)


@extend_schema_view(
    list=extend_schema(
        tags=["Inventory - Logs"],
        summary="List inventory log entries",
        description="Read-only audit trail of every stock movement (check-ins, check-outs, sales).",
        parameters=[
            OpenApiParameter("product", OpenApiTypes.UUID, OpenApiParameter.QUERY, description="Filter by product UUID."),
            OpenApiParameter(
                "action",
                OpenApiTypes.STR,
                OpenApiParameter.QUERY,
                description="Filter by action type.",
                enum=[choice[0] for choice in InventoryLog.ACTION_CHOICES],
            ),
            OpenApiParameter("staff", OpenApiTypes.UUID, OpenApiParameter.QUERY, description="Filter by staff user UUID."),
            OpenApiParameter("date_from", OpenApiTypes.DATE, OpenApiParameter.QUERY, description="Filter logs created on or after this date (YYYY-MM-DD)."),
            OpenApiParameter("date_to", OpenApiTypes.DATE, OpenApiParameter.QUERY, description="Filter logs created on or before this date (YYYY-MM-DD)."),
            OpenApiParameter("search", OpenApiTypes.STR, OpenApiParameter.QUERY, description="Search in notes."),
            OpenApiParameter("ordering", OpenApiTypes.STR, OpenApiParameter.QUERY, description="Order by: created_at, action, quantity (prefix `-` for descending)."),
        ],
    ),
    retrieve=extend_schema(tags=["Inventory - Logs"], summary="Get a log entry"),
)
class InventoryLogViewSet(BaseModelViewSet):
    serializer_class = InventoryLogSerializer
    queryset = InventoryLog.objects.select_related("product__brand", "staff").all()
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
                total_quantity=Coalesce(Sum("quantity"), 0),
            )
            .order_by("brand_name", "model")
        )

        paginator = self.pagination_class()
        page = paginator.paginate_queryset(rows, request, view=self)

        result = [
            {
                "slug": row["slug"],
                "brand_name": row["brand_name"],
                "model": row["model"],
                "color": row["colors"],
                "size": row["sizes"],
                "barcode": row["barcodes"],
                "quantity": row["total_quantity"],
                "image": row.get("image"),
            }
            for row in page
        ]

        return paginator.get_paginated_response(result)


@extend_schema(
    tags=["Inventory - Products"],
    summary="Export products to Excel",
    description=(
        "Streams the filtered product catalog as an `.xlsx` workbook. "
        "Accepts the same query string filters as the product list endpoint "
        "(brand, model, size, color, barcode, is_published)."
    ),
    parameters=[
        OpenApiParameter("brand", OpenApiTypes.STR, OpenApiParameter.QUERY),
        OpenApiParameter("model", OpenApiTypes.STR, OpenApiParameter.QUERY),
        OpenApiParameter("size", OpenApiTypes.STR, OpenApiParameter.QUERY),
        OpenApiParameter("color", OpenApiTypes.STR, OpenApiParameter.QUERY),
        OpenApiParameter("is_published", OpenApiTypes.BOOL, OpenApiParameter.QUERY),
    ],
    responses={(200, "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"): OpenApiTypes.BINARY},
)
class ProductExcelExportAPIView(ExcelExportAPIView):
    queryset = Product.objects.select_related("brand", "vendor").all()
    permission_classes = [IsAuthenticated]
    filterset_class = ProductFilter
    serializer_class = ProductSerializer

    excel_sheet_name = "Products"
    excel_filename_prefix = "products"
    excel_export_fields = [
        ("Product ID", "id"),
        ("Brand", "brand__name"),
        ("Model", "model"),
        ("Size", "size"),
        ("Color", "color"),
        ("Barcode", "barcode"),
        ("Vendor", "vendor__name"),
        ("Selling Price", "selling_price"),
        ("Quantity", "quantity"),
        ("Low Stock Threshold", "low_stock_threshold"),
        ("Published", "is_published"),
        ("Archived", "is_archived"),
        ("Created At", "created_at"),
    ]
