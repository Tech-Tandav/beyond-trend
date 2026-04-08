from django.db.models import (
    Count,
    DecimalField,
    ExpressionWrapper,
    F,
    IntegerField,
    Q,
    Sum,
    Value,
)
from django.db.models.functions import Coalesce
from drf_spectacular.utils import OpenApiResponse, extend_schema
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from beyond_trend.inventory.models import InventoryLog, Product


@extend_schema(
    tags=["Inventory - Analytics"],
    summary="Inventory snapshot",
    description=(
        "Returns a snapshot of the current inventory state, including:\n"
        "- **summary**: total products, units, stock value, low-stock and out-of-stock counts\n"
        "- **stock_by_brand**: per-brand units and stock value\n"
        "- **top_stocked_products**: top 10 variants by quantity\n"
        "- **low_stock_items**: variants below their per-product threshold\n"
        "- **out_of_stock_items**: variants with zero stock\n"
        "- **recent_activity**: last 10 stock movements"
    ),
    responses={200: OpenApiResponse(description="Inventory analytics payload (see description).")},
)
class InventoryAnalyticsView(APIView):
    """
    GET /api/v1/inventory/analytics/

    Returns a snapshot of the current inventory state.
    Stock levels come from the Product.quantity field and low-stock thresholds
    are evaluated per-product.
    """

    permission_classes = [IsAuthenticated]

    def get(self, request):
        qty = Coalesce(F("quantity"), Value(0), output_field=IntegerField())
        stock_value_expr = ExpressionWrapper(
            F("selling_price") * qty,
            output_field=DecimalField(max_digits=14, decimal_places=2),
        )

        base_qs = Product.objects.select_related("brand").annotate(
            qty=qty,
            stock_value=stock_value_expr,
        )

        # --- Summary (single aggregate query) ---
        summary_agg = base_qs.aggregate(
            total_products=Count("id"),
            total_units=Coalesce(Sum("qty"), Value(0)),
            total_stock_value=Coalesce(
                Sum("stock_value"),
                Value(0),
                output_field=DecimalField(max_digits=14, decimal_places=2),
            ),
            low_stock_count=Count(
                "id",
                filter=Q(qty__gt=0, qty__lte=F("low_stock_threshold")),
            ),
            out_of_stock_count=Count("id", filter=Q(qty=0)),
        )

        # --- Stock by brand ---
        stock_by_brand = list(
            base_qs.values("brand__name")
            .annotate(
                products=Count("id"),
                units=Coalesce(Sum("qty"), Value(0)),
                stock_value=Coalesce(
                    Sum("stock_value"),
                    Value(0),
                    output_field=DecimalField(max_digits=14, decimal_places=2),
                ),
            )
            .order_by("-stock_value")
        )

        # --- Top stocked products ---
        top_stocked = list(
            base_qs.order_by("-qty").values(
                "barcode",
                "brand__name",
                "model",
                "size",
                "color",
                "qty",
                "selling_price",
                "stock_value",
            )[:10]
        )

        # --- Low stock items (per-product threshold) ---
        low_stock_items = list(
            base_qs.filter(qty__gt=0, qty__lte=F("low_stock_threshold"))
            .order_by("qty")
            .values(
                "barcode",
                "brand__name",
                "model",
                "size",
                "color",
                "qty",
                "low_stock_threshold",
                "selling_price",
            )
        )

        # --- Out of stock items ---
        out_of_stock_items = list(
            base_qs.filter(qty=0).values(
                "barcode",
                "brand__name",
                "model",
                "size",
                "color",
                "selling_price",
            )
        )

        # --- Recent activity (last 10 inventory movements) ---
        recent_activity = list(
            InventoryLog.objects.select_related("product__brand", "staff")
            .order_by("-created_at")
            .values(
                "action",
                "quantity",
                "notes",
                "created_at",
                "product__barcode",
                "product__brand__name",
                "product__model",
                "staff__username",
            )[:10]
        )

        return Response(
            {
                "summary": summary_agg,
                "stock_by_brand": [
                    {
                        "brand_name": row["brand__name"],
                        "products": row["products"],
                        "units": row["units"],
                        "stock_value": row["stock_value"],
                    }
                    for row in stock_by_brand
                ],
                "top_stocked_products": [
                    {
                        "barcode": row["barcode"],
                        "brand_name": row["brand__name"],
                        "model": row["model"],
                        "size": row["size"],
                        "color": row["color"],
                        "quantity": row["qty"],
                        "selling_price": row["selling_price"],
                        "stock_value": row["stock_value"],
                    }
                    for row in top_stocked
                ],
                "low_stock_items": [
                    {
                        "barcode": row["barcode"],
                        "brand_name": row["brand__name"],
                        "model": row["model"],
                        "size": row["size"],
                        "color": row["color"],
                        "quantity": row["qty"],
                        "low_stock_threshold": row["low_stock_threshold"],
                        "selling_price": row["selling_price"],
                    }
                    for row in low_stock_items
                ],
                "out_of_stock_items": [
                    {
                        "barcode": row["barcode"],
                        "brand_name": row["brand__name"],
                        "model": row["model"],
                        "size": row["size"],
                        "color": row["color"],
                        "selling_price": row["selling_price"],
                    }
                    for row in out_of_stock_items
                ],
                "recent_activity": [
                    {
                        "action": row["action"],
                        "quantity": row["quantity"],
                        "notes": row["notes"],
                        "created_at": row["created_at"],
                        "barcode": row["product__barcode"],
                        "brand_name": row["product__brand__name"],
                        "model": row["product__model"],
                        "staff": row["staff__username"],
                    }
                    for row in recent_activity
                ],
            }
        )
