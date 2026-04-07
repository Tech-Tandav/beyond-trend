from datetime import date, timedelta

from django.db.models import Count, DecimalField, ExpressionWrapper, F, Sum, Value
from django.db.models.functions import Coalesce, TruncDate
from django.utils import timezone
from drf_spectacular.utils import OpenApiParameter, OpenApiResponse, extend_schema
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from beyond_trend.sales.models import Sale, SaleItem


def _get_date_range(request):
    """
    Resolve date range from query params.
    Priority: from_date+to_date > period > default (month)
    """
    from_date = request.query_params.get("from_date")
    to_date = request.query_params.get("to_date")

    if from_date and to_date:
        try:
            return date.fromisoformat(from_date), date.fromisoformat(to_date)
        except ValueError:
            pass

    period = request.query_params.get("period", "month")
    today = timezone.localdate()

    if period == "today":
        return today, today
    if period == "week":
        return today - timedelta(days=6), today
    if period == "year":
        return today.replace(month=1, day=1), today
    # month (default)
    return today.replace(day=1), today


@extend_schema(
    tags=["Sales - Analytics"],
    summary="Sales analytics dashboard",
    description=(
        "Returns sales KPIs over a date range. The range is resolved from the query "
        "parameters in this order of priority:\n\n"
        "1. `from_date` + `to_date` (ISO `YYYY-MM-DD`)\n"
        "2. `period` (one of: `today`, `week`, `month`, `year`)\n"
        "3. Default: current month\n\n"
        "The payload includes totals, daily trend, top selling products, and sales by staff."
    ),
    parameters=[
        OpenApiParameter("from_date", str, description="Start date (YYYY-MM-DD). Used together with `to_date`."),
        OpenApiParameter("to_date", str, description="End date (YYYY-MM-DD). Used together with `from_date`."),
        OpenApiParameter(
            "period",
            str,
            description="Preset range. One of `today`, `week`, `month`, `year`.",
            enum=["today", "week", "month", "year"],
        ),
    ],
    responses={200: OpenApiResponse(description="Sales analytics payload (see description).")},
)
class SalesAnalyticsView(APIView):
    """
    GET /api/v1/sales/analytics/
    """

    permission_classes = [IsAuthenticated]

    def get(self, request):
        from_date, to_date = _get_date_range(request)

        sales_qs = Sale.objects.filter(
            created_at__date__gte=from_date,
            created_at__date__lte=to_date,
        )
        items_qs = SaleItem.objects.filter(
            sale__created_at__date__gte=from_date,
            sale__created_at__date__lte=to_date,
        )

        decimal_field = DecimalField(max_digits=14, decimal_places=2)
        zero_decimal = Value(0, output_field=decimal_field)

        # --- Summary ---
        sales_agg = sales_qs.aggregate(
            total_revenue=Coalesce(Sum("total_amount"), zero_decimal),
            total_sales=Count("id"),
        )
        units_agg = items_qs.aggregate(
            total_units=Coalesce(Sum("quantity"), Value(0)),
        )
        total_revenue = sales_agg["total_revenue"] or 0
        total_sales = sales_agg["total_sales"] or 0
        total_units = units_agg["total_units"] or 0
        avg_sale_value = (
            round(float(total_revenue) / total_sales, 2) if total_sales else 0
        )

        # --- Revenue trend (daily) ---
        trend = list(
            sales_qs.annotate(date=TruncDate("created_at"))
            .values("date")
            .annotate(
                revenue=Coalesce(Sum("total_amount"), zero_decimal),
                sales_count=Count("id"),
            )
            .order_by("date")
        )
        units_by_date = {
            row["date"]: row["units_sold"]
            for row in items_qs.annotate(date=TruncDate("sale__created_at"))
            .values("date")
            .annotate(units_sold=Sum("quantity"))
        }

        # --- Top products by units sold ---
        line_revenue_expr = ExpressionWrapper(
            F("quantity") * F("selling_price"),
            output_field=decimal_field,
        )
        top_products_qs = (
            items_qs.values(
                "product_id",
                "product__barcode",
                "product__brand__name",
                "product__model",
                "product__size",
                "product__color",
            )
            .annotate(
                units_sold=Sum("quantity"),
                revenue=Coalesce(Sum(line_revenue_expr), zero_decimal),
            )
            .order_by("-units_sold")[:10]
        )

        top_products = [
            {
                "product_id": str(row["product_id"]),
                "barcode": row["product__barcode"],
                "brand_name": row["product__brand__name"],
                "model": row["product__model"],
                "size": row["product__size"],
                "color": row["product__color"],
                "units_sold": row["units_sold"],
                "revenue": row["revenue"],
            }
            for row in top_products_qs
        ]

        # --- Sales by staff ---
        sales_by_staff = list(
            sales_qs.values("staff__id", "staff__name", "staff__username", "staff__email")
            .annotate(
                sales_count=Count("id"),
                revenue=Coalesce(Sum("total_amount"), zero_decimal),
            )
            .order_by("-revenue")
        )

        return Response(
            {
                "period": {
                    "from_date": str(from_date),
                    "to_date": str(to_date),
                },
                "summary": {
                    "total_revenue": total_revenue,
                    "total_sales": total_sales,
                    "total_units_sold": total_units,
                    "average_sale_value": avg_sale_value,
                },
                "revenue_trend": [
                    {
                        "date": str(row["date"]),
                        "revenue": row["revenue"],
                        "sales_count": row["sales_count"],
                        "units_sold": units_by_date.get(row["date"], 0),
                    }
                    for row in trend
                ],
                "top_products": top_products,
                "sales_by_staff": [
                    {
                        "staff_id": str(row["staff__id"]) if row["staff__id"] else None,
                        "staff_name": (
                            (row["staff__name"] or "").strip()
                            or row["staff__username"]
                            or row["staff__email"]
                        ),
                        "sales_count": row["sales_count"],
                        "revenue": row["revenue"],
                    }
                    for row in sales_by_staff
                ],
            }
        )
