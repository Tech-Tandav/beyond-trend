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

from beyond_trend.inventory.models import (
    Brand,
    Category,
    InventoryLog,
    Product,
    SubCategory,
    Vendor,
)
from beyond_trend.inventory.api.filters import InventoryLogFilter, ProductFilter
from beyond_trend.inventory.api.serializers import (
    BrandSerializer,
    CategorySerializer,
    CheckInSerializer,
    CheckOutSerializer,
    InventoryLogSerializer,
    ProductSerializer,
    SubCategorySerializer,
    VendorSerializer,
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

    def get_permissions(self):
        if self.action in ("list", "retrieve"):
            return [AllowAny()]
        return super().get_permissions()


@extend_schema_view(
    list=extend_schema(tags=["Inventory - Categories"], summary="List categories"),
    retrieve=extend_schema(tags=["Inventory - Categories"], summary="Get a category"),
    create=extend_schema(tags=["Inventory - Categories"], summary="Create a category"),
    update=extend_schema(tags=["Inventory - Categories"], summary="Replace a category"),
    partial_update=extend_schema(tags=["Inventory - Categories"], summary="Patch a category"),
    destroy=extend_schema(tags=["Inventory - Categories"], summary="Archive a category"),
)
class CategoryViewSet(BaseModelViewSet):
    serializer_class = CategorySerializer
    queryset = Category.objects.prefetch_related("subcategories").all()
    permission_classes = [IsAuthenticated]
    search_fields = ["name"]
    ordering_fields = ["name", "created_at"]
    filterset_fields = ["is_active", "is_archived"]

    def get_permissions(self):
        if self.action in ("list", "retrieve"):
            return [AllowAny()]
        return super().get_permissions()


@extend_schema_view(
    list=extend_schema(tags=["Inventory - Sub Categories"], summary="List sub categories"),
    retrieve=extend_schema(tags=["Inventory - Sub Categories"], summary="Get a sub category"),
    create=extend_schema(tags=["Inventory - Sub Categories"], summary="Create a sub category"),
    update=extend_schema(tags=["Inventory - Sub Categories"], summary="Replace a sub category"),
    partial_update=extend_schema(tags=["Inventory - Sub Categories"], summary="Patch a sub category"),
    destroy=extend_schema(tags=["Inventory - Sub Categories"], summary="Archive a sub category"),
)
class SubCategoryViewSet(BaseModelViewSet):
    serializer_class = SubCategorySerializer
    queryset = SubCategory.objects.select_related("category").all()
    permission_classes = [IsAuthenticated]
    search_fields = ["name", "category__name"]
    ordering_fields = ["name", "created_at"]
    filterset_fields = ["category", "is_active", "is_archived"]

    def get_permissions(self):
        if self.action in ("list", "retrieve"):
            return [AllowAny()]
        return super().get_permissions()


@extend_schema(
    tags=["Inventory - Products"],
    summary="List products",
    description=(
        "Returns a paginated list of product variants. Each row represents a unique "
        "**brand + model + size + color** combination.\n\n"
        "Supports filtering via `ProductFilter`, full-text search on "
        "`model`, `description`, `brand__name`, `barcode`, and "
        "ordering by `model`, `created_at`."
    ),
    parameters=[
        OpenApiParameter("brand", OpenApiTypes.STR, OpenApiParameter.QUERY, description="Filter by brand slug (exact match)."),
        OpenApiParameter("model", OpenApiTypes.STR, OpenApiParameter.QUERY, description="Filter by model name (case-insensitive contains)."),
        OpenApiParameter("is_published", OpenApiTypes.BOOL, OpenApiParameter.QUERY, description="Filter by published flag."),
        OpenApiParameter("barcode", OpenApiTypes.STR, OpenApiParameter.QUERY, description="Filter by barcode (case-insensitive exact)."),
        OpenApiParameter("size", OpenApiTypes.STR, OpenApiParameter.QUERY, description="Filter by size (exact element match within the size array)."),
        OpenApiParameter("color", OpenApiTypes.STR, OpenApiParameter.QUERY, description="Filter by color (exact element match within the color array)."),
        OpenApiParameter("search", OpenApiTypes.STR, OpenApiParameter.QUERY, description="Free-text search across model, description, brand name, barcode."),
        OpenApiParameter("ordering", OpenApiTypes.STR, OpenApiParameter.QUERY, description="Order by: model, created_at (prefix `-` for descending)."),
    ],
)
class ProductListView(generics.ListAPIView):
    serializer_class = ProductSerializer
    queryset = Product.objects.select_related("brand", "category", "subcategory").all()
    permission_classes = [AllowAny]
    filterset_class = ProductFilter
    search_fields = ["model", "description", "brand__name", "barcode"]
    ordering_fields = ["model", "created_at"]


@extend_schema(
    tags=["Inventory - Products"],
    summary="Create a product variant",
    description="Creates a new product variant. The `slug` field is auto-generated from brand + model + size + color.",
)
class ProductCreateView(generics.CreateAPIView):
    serializer_class = ProductSerializer
    queryset = Product.objects.select_related("brand", "category", "subcategory").all()
    permission_classes = [IsAuthenticated]


@extend_schema(
    tags=["Inventory - Products"],
    summary="Get a product variant by slug",
)
class ProductRetrieveView(generics.RetrieveAPIView):
    serializer_class = ProductSerializer
    queryset = Product.objects.select_related("brand", "category", "subcategory").all()
    permission_classes = [AllowAny]
    lookup_field = "barcode"


@extend_schema(
    tags=["Inventory - Products"],
    summary="Update a product variant",
)
class ProductUpdateView(generics.UpdateAPIView):
    serializer_class = ProductSerializer
    queryset = Product.objects.select_related("brand", "category", "subcategory").all()
    permission_classes = [IsAuthenticated]
    lookup_field = "slug"

    def update(self, request, *args, **kwargs):
        instance = self.get_object()
        # Snapshot current values for fields being sent
        old_values = {}
        for field in request.data:
            if hasattr(instance, field):
                old_values[field] = getattr(instance, field)

        response = super().update(request, *args, **kwargs)

        # Determine which fields actually changed
        instance.refresh_from_db()
        updated_fields = []
        for field, old_val in old_values.items():
            new_val = getattr(instance, field, None)
            if str(old_val) != str(new_val):
                updated_fields.append(field)

        response.data["updated_fields"] = updated_fields
        return response


@extend_schema(
    tags=["Inventory - Products"],
    summary="Delete a product variant",
)
class ProductDestroyView(generics.DestroyAPIView):
    serializer_class = ProductSerializer
    queryset = Product.objects.select_related("brand", "category", "subcategory").all()
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


@extend_schema(
    tags=["Inventory - Products"],
    summary="List available sizes",
    description="Returns a list of distinct product sizes currently in use, sorted alphabetically. Supports filtering by category, subcategory, and brand.",
    parameters=[
        OpenApiParameter("category_name", OpenApiTypes.STR, OpenApiParameter.QUERY, description="Filter by category name (case-insensitive partial match)."),
        OpenApiParameter("subcategory_name", OpenApiTypes.STR, OpenApiParameter.QUERY, description="Filter by subcategory name (case-insensitive partial match)."),
        OpenApiParameter("brand_name", OpenApiTypes.STR, OpenApiParameter.QUERY, description="Filter by brand name (case-insensitive partial match)."),
    ],
    responses={200: inline_serializer(
        name="SizeListResponse",
        fields={"sizes": serializers.ListField(child=serializers.CharField())},
    )},
)
class SizeListView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        qs = Product.objects.exclude(size=[])

        category_name = request.query_params.get("category_name")
        if category_name:
            qs = qs.filter(category__name__icontains=category_name)

        subcategory_name = request.query_params.get("subcategory_name")
        if subcategory_name:
            qs = qs.filter(subcategory__name__icontains=subcategory_name)

        brand_name = request.query_params.get("brand_name")
        if brand_name:
            qs = qs.filter(brand__name__icontains=brand_name)

        sizes = sorted({s for row in qs.values_list("size", flat=True) for s in row if s})
        return Response({"sizes": sizes})


class PublicInventoryItemSerializer(serializers.Serializer):
    slug = serializers.CharField()
    brand_name = serializers.CharField()
    category_name = serializers.CharField(allow_blank=True)
    subcategory_name = serializers.CharField(allow_blank=True)
    model = serializers.CharField()
    color = serializers.ListField(child=serializers.CharField())
    size = serializers.ListField(child=serializers.CharField())
    barcode = serializers.ListField(child=serializers.CharField())
    quantity = serializers.IntegerField()
    image = serializers.CharField(allow_null=True)
    images = serializers.ListField(child=serializers.CharField())


@extend_schema(
    tags=["Inventory - Public"],
    summary="Public catalog (grouped by brand + model)",
    description=(
        "Public, unauthenticated endpoint. Aggregates published variants by `brand + model` "
        "and returns the available colors, sizes, and total quantity in stock. Used by the "
        "storefront to render product cards.\n\n"
        "Supports filtering by category, subcategory, brand (by slug), color, size, "
        "and free-text search."
    ),
    parameters=[
        OpenApiParameter("category", OpenApiTypes.STR, OpenApiParameter.QUERY, description="Filter by category slug."),
        OpenApiParameter("category_name", OpenApiTypes.STR, OpenApiParameter.QUERY, description="Filter by category name (case-insensitive partial match)."),
        OpenApiParameter("subcategory", OpenApiTypes.STR, OpenApiParameter.QUERY, description="Filter by subcategory slug."),
        OpenApiParameter("subcategory_name", OpenApiTypes.STR, OpenApiParameter.QUERY, description="Filter by subcategory name (case-insensitive partial match)."),
        OpenApiParameter("brand", OpenApiTypes.STR, OpenApiParameter.QUERY, description="Filter by brand slug."),
        OpenApiParameter("brand_name", OpenApiTypes.STR, OpenApiParameter.QUERY, description="Filter by brand name (case-insensitive partial match)."),
        OpenApiParameter("color", OpenApiTypes.STR, OpenApiParameter.QUERY, description="Filter by color (case-insensitive partial match)."),
        OpenApiParameter("size", OpenApiTypes.STR, OpenApiParameter.QUERY, description="Filter by size (exact match)."),
        OpenApiParameter("is_featured", OpenApiTypes.BOOL, OpenApiParameter.QUERY, description="Filter by featured flag."),
        OpenApiParameter("show_in_website", OpenApiTypes.BOOL, OpenApiParameter.QUERY, description="Filter by show in website flag."),
        OpenApiParameter("search", OpenApiTypes.STR, OpenApiParameter.QUERY, description="Search across model, brand name, description."),
        OpenApiParameter("ordering", OpenApiTypes.STR, OpenApiParameter.QUERY, description="Order by: created_at, -created_at, updated_at, -updated_at, model, -model, brand_name, -brand_name, category_name, -category_name."),
    ],
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
        from django.db.models import OuterRef, Subquery

        from beyond_trend.inventory.models import ProductImage

        primary_image = ProductImage.objects.filter(
            product=OuterRef("pk"),
        ).order_by("-is_primary", "order", "created_at").values("image")[:1]

        qs = Product.objects.filter(is_published=True)

        # Apply filters from query params
        category = request.query_params.get("category")
        if category:
            qs = qs.filter(category__slug=category)

        category_name = request.query_params.get("category_name")
        if category_name:
            qs = qs.filter(category__name__icontains=category_name)

        subcategory = request.query_params.get("subcategory")
        if subcategory:
            qs = qs.filter(subcategory__slug=subcategory)

        subcategory_name = request.query_params.get("subcategory_name")
        if subcategory_name:
            qs = qs.filter(subcategory__name__icontains=subcategory_name)

        brand = request.query_params.get("brand")
        if brand:
            qs = qs.filter(brand__slug=brand)

        brand_name = request.query_params.get("brand_name")
        if brand_name:
            qs = qs.filter(brand__name__icontains=brand_name)

        color = request.query_params.get("color")
        if color:
            qs = qs.filter(color__contains=[color])

        size = request.query_params.get("size")
        if size:
            qs = qs.filter(size__contains=[size])

        is_featured = request.query_params.get("is_featured")
        if is_featured is not None:
            qs = qs.filter(is_featured=is_featured.lower() in ("true", "1"))

        show_in_website = request.query_params.get("show_in_website")
        if show_in_website is not None:
            qs = qs.filter(show_in_website=show_in_website.lower() in ("true", "1"))

        search = request.query_params.get("search")
        if search:
            from django.db.models import Q
            qs = qs.filter(
                Q(model__icontains=search)
                | Q(brand__name__icontains=search)
                | Q(description__icontains=search)
            )

        # Ordering
        ALLOWED_ORDERING = {
            "created_at", "-created_at",
            "updated_at", "-updated_at",
            "model", "-model",
            "brand_name", "-brand_name",
            "category_name", "-category_name",
        }
        ordering_param = request.query_params.get("ordering")

        rows = (
            qs
            .annotate(primary_image=Subquery(primary_image))
            .values(
                "pk",
                "slug",
                "model",
                "updated_at",
                "primary_image",
                brand_name=Coalesce("brand__name", Value("")),
                category_name=Coalesce("category__name", Value("")),
                subcategory_name=Coalesce("subcategory__name", Value("")),
                vendor_name=Coalesce("vendor__name", Value("")),
            )
            .annotate(
                colors=ArrayAgg("color", distinct=True),
                sizes=ArrayAgg("size", distinct=True),
                barcodes=ArrayAgg("barcode", distinct=True, ordering="barcode"),
                total_quantity=Coalesce(Sum("quantity"), 0),
            )
        )

        if ordering_param and ordering_param in ALLOWED_ORDERING:
            rows = rows.order_by(ordering_param)
        else:
            rows = rows.order_by("category_name", "subcategory_name", "brand_name", "model")

        paginator = self.pagination_class()
        page = paginator.paginate_queryset(rows, request, view=self)

        from django.conf import settings as dj_settings

        def build_image_url(image_path):
            if not image_path:
                return None
            if image_path.startswith(("http://", "https://")):
                return request.build_absolute_uri(image_path)
            media_url = dj_settings.MEDIA_URL or "/media/"
            if not media_url.endswith("/"):
                media_url += "/"
            return request.build_absolute_uri(f"{media_url}{image_path.lstrip('/')}")

        product_pks = [row["pk"] for row in page]
        images_by_product: dict[int, list[str]] = {}
        for img in (
            ProductImage.objects.filter(product_id__in=product_pks)
            .order_by("product_id", "-is_primary", "order", "created_at")
            .values("product_id", "image")
        ):
            url = build_image_url(img["image"])
            if url:
                images_by_product.setdefault(img["product_id"], []).append(url)

        result = [
            {
                "slug": row["slug"],
                "brand_name": row["brand_name"],
                "category_name": row["category_name"],
                "subcategory_name": row["subcategory_name"],
                "vendor_name": row["vendor_name"],
                "model": row["model"],
                "color": sorted({c for arr in (row["colors"] or []) if arr for c in arr if c}),
                "size": sorted({s for arr in (row["sizes"] or []) if arr for s in arr if s}),
                "barcode": row["barcodes"],
                "quantity": row["total_quantity"],
                "updated_at": row["updated_at"],
                "image": build_image_url(row.get("primary_image")),
                "images": images_by_product.get(row["pk"], []),
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
        ("Size", "size_display"),
        ("Color", "color_display"),
        ("Barcode", "barcode"),
        ("Vendor", "vendor__name"),
        ("Selling Price", "selling_price"),
        ("Quantity", "quantity"),
        ("Low Stock Threshold", "low_stock_threshold"),
        ("Published", "is_published"),
        ("Archived", "is_archived"),
        ("Created At", "created_at"),
    ]
