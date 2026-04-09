from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import (
    OpenApiExample,
    OpenApiParameter,
    OpenApiResponse,
    extend_schema,
    extend_schema_view,
)
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from beyond_trend.core.excel import ExcelExportAPIView
from beyond_trend.core.viewsets import BaseModelViewSet

from beyond_trend.sales.models import Sale
from beyond_trend.sales.api.filters import SaleFilter
from beyond_trend.sales.api.serializers import CheckoutSerializer, SaleSerializer
from beyond_trend.sales.api.usecases import CheckoutUseCase


@extend_schema_view(
    list=extend_schema(
        tags=["Sales"],
        summary="List sales",
        description=(
            "Returns a paginated list of POS sales (read-only).\n\n"
            "Supports filtering via `SaleFilter`, `?search=` on staff name, "
            "and `?ordering=` on `created_at`, `total_amount`, `subtotal`."
        ),
        parameters=[
            OpenApiParameter("staff", OpenApiTypes.UUID, OpenApiParameter.QUERY, description="Filter by staff user UUID."),
            OpenApiParameter("date_from", OpenApiTypes.DATE, OpenApiParameter.QUERY, description="Filter sales on or after this date (YYYY-MM-DD)."),
            OpenApiParameter("date_to", OpenApiTypes.DATE, OpenApiParameter.QUERY, description="Filter sales on or before this date (YYYY-MM-DD)."),
            OpenApiParameter("search", OpenApiTypes.STR, OpenApiParameter.QUERY, description="Search across staff name."),
            OpenApiParameter("ordering", OpenApiTypes.STR, OpenApiParameter.QUERY, description="Order by: created_at, total_amount, subtotal (prefix `-` for descending)."),
        ],
    ),
    retrieve=extend_schema(
        tags=["Sales"],
        summary="Get a sale",
        description="Retrieve a single sale with its line items.",
    ),
    create=extend_schema(
        tags=["Sales"],
        summary="Create a sale (raw)",
        description="Direct sale creation. Most clients should use the `/sales/checkout/` action instead, which validates stock.",
    ),
)
class SaleViewSet(BaseModelViewSet):
    serializer_class = SaleSerializer
    queryset = Sale.objects.all()
    permission_classes = [IsAuthenticated]
    http_method_names = ["get", "head", "options", "post"]
    filterset_class = SaleFilter
    search_fields = ["staff__name"]
    ordering_fields = ["created_at", "total_amount", "subtotal"]

    @extend_schema(
        tags=["Sales"],
        summary="POS checkout",
        description=(
            "Full point-of-sale checkout. In a single transaction this endpoint:\n\n"
            "1. Validates stock for every line item.\n"
            "2. Creates a `Sale` and the related `SaleItem` rows.\n"
            "3. Decrements stock and writes `InventoryLog` check-out entries.\n\n"
            "Returns the full sale on success. Returns `400` if any line item has "
            "insufficient stock."
        ),
        request=CheckoutSerializer,
        responses={
            201: SaleSerializer,
            400: OpenApiResponse(description="Validation error: insufficient stock."),
        },
        examples=[
            OpenApiExample(
                "Walk-in checkout",
                value={
                    "items": [
                        {
                            "product_id": "0d3b3ce6-1b9f-4f1d-8f5d-6f1a2c2d3e4f",
                            "quantity": 1,
                            "selling_price": "4500.00",
                        }
                    ],
                    "notes": "",
                },
                request_only=True,
            ),
        ],
    )
    @action(detail=False, methods=["post"], url_path="checkout")
    def checkout(self, request):
        """
        POS Checkout:
        - Validates stock for all items
        - Creates Sale + SaleItems
        - Reduces stock
        - Logs inventory check-out
        """
        serializer = CheckoutSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        use_case = CheckoutUseCase(data=serializer.validated_data, staff=request.user)
        sale = use_case.execute()
        return Response(
            SaleSerializer(sale, context=self.get_serializer_context()).data,
            status=status.HTTP_201_CREATED,
        )


@extend_schema(
    tags=["Sales"],
    summary="Export sales to Excel",
    description=(
        "Streams the filtered sales list as an `.xlsx` workbook with two sheets: "
        "`Sales` (one row per sale) and `Sale Items` (one row per line item). "
        "Accepts the same filters as the sales list endpoint."
    ),
    parameters=[
        OpenApiParameter("staff", OpenApiTypes.UUID, OpenApiParameter.QUERY),
        OpenApiParameter("date_from", OpenApiTypes.DATE, OpenApiParameter.QUERY),
        OpenApiParameter("date_to", OpenApiTypes.DATE, OpenApiParameter.QUERY),
    ],
    responses={(200, "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"): OpenApiTypes.BINARY},
)
class SaleExcelExportAPIView(ExcelExportAPIView):
    queryset = Sale.objects.select_related("staff").prefetch_related(
        "items__product"
    )
    permission_classes = [IsAuthenticated]
    filterset_class = SaleFilter
    serializer_class = SaleSerializer

    excel_sheet_name = "Sales"
    excel_filename_prefix = "sales"
    excel_export_fields = [
        ("Sale ID", "id"),
        ("Staff", "staff"),
        ("Subtotal", "subtotal"),
        ("Discount", "discount_amount"),
        ("Total", "total_amount"),
        ("Notes", "notes"),
        ("Created At", "created_at"),
    ]

    def get_excel_sheets(self, queryset):
        sheets = super().get_excel_sheets(queryset)
        item_rows = []
        for sale in queryset:
            for item in sale.items.all():
                item_rows.append([
                    str(sale.id),
                    str(item.product),
                    item.quantity,
                    item.selling_price,
                    item.total,
                ])
        sheets.append({
            "name": "Sale Items",
            "headers": ["Sale ID", "Product", "Quantity", "Selling Price", "Line Total"],
            "rows": item_rows,
        })
        return sheets