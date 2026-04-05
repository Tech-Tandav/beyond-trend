from datetime import timedelta

from django.db.models import Count, DecimalField, ExpressionWrapper, F, Sum
from django.db.models.functions import TruncDate
from django.utils import timezone
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from beyond_trend.inventory.models import ShoeProduct
from beyond_trend.sales.models import ShoeSale


def _get_date_range(request):
    """
    Resolve date range from query params.
    Priority: from_date+to_date > period > default (month)
    """
    from_date = request.query_params.get("from_date")
    to_date = request.query_params.get("to_date")

    if from_date and to_date:
        from datetime import date
        return date.fromisoformat(from_date), date.fromisoformat(to_date)

    period = request.query_params.get("period", "month")
    today = timezone.localdate()

    if period == "today":
        return today, today
    elif period == "week":
        return today - timedelta(days=6), today
    elif period == "year":
        return today.replace(month=1, day=1), today
    else:  # month (default)
        return today.replace(day=1), today


class SalesAnalyticsView(APIView):
    """
    GET /api/v1/sales/analytics/

    Query params:
      period   : today | week | month (default) | year
      from_date: YYYY-MM-DD  (overrides period)
      to_date  : YYYY-MM-DD  (overrides period)
    """

    permission_classes = [IsAuthenticated]

    def get(self, request):
        from_date, to_date = _get_date_range(request)

        qs = ShoeSale.objects.filter(
            created_at__date__gte=from_date,
            created_at__date__lte=to_date,
        )

        # Annotate revenue per sale row = quantity * selling_price
        qs = qs.annotate(
            revenue=ExpressionWrapper(
                F("quantity") * F("selling_price"),
                output_field=DecimalField(max_digits=14, decimal_places=2),
            )
        )

        # --- Summary ---
        agg = qs.aggregate(
            total_revenue=Sum("revenue"),
            total_sales=Count("id"),
            total_units=Sum("quantity"),
        )
        total_revenue = agg["total_revenue"] or 0
        total_sales = agg["total_sales"] or 0
        total_units = agg["total_units"] or 0
        avg_sale_value = round(total_revenue / total_sales, 2) if total_sales else 0

        # --- Revenue trend (daily) ---
        trend = (
            qs.annotate(date=TruncDate("created_at"))
            .values("date")
            .annotate(
                revenue=Sum(
                    ExpressionWrapper(
                        F("quantity") * F("selling_price"),
                        output_field=DecimalField(max_digits=14, decimal_places=2),
                    )
                ),
                sales_count=Count("id"),
                units_sold=Sum("quantity"),
            )
            .order_by("date")
        )

        # --- Top products by units sold ---
        top_products_qs = (
            qs.values("bar_code")
            .annotate(
                units_sold=Sum("quantity"),
                revenue=Sum(
                    ExpressionWrapper(
                        F("quantity") * F("selling_price"),
                        output_field=DecimalField(max_digits=14, decimal_places=2),
                    )
                ),
            )
            .order_by("-units_sold")[:10]
        )

        # Enrich top products with ShoeProduct info
        barcodes = [r["bar_code"] for r in top_products_qs]
        shoe_map = {
            s.barcode: s
            for s in ShoeProduct.objects.filter(barcode__in=barcodes)
        }

        top_products = []
        for row in top_products_qs:
            shoe = shoe_map.get(row["bar_code"])
            top_products.append(
                {
                    "barcode": row["bar_code"],
                    "brand_name": shoe.brand_name if shoe else None,
                    "size": shoe.size if shoe else None,
                    "color": shoe.color if shoe else None,
                    "units_sold": row["units_sold"],
                    "revenue": row["revenue"],
                }
            )

        # --- Sales by staff ---
        sales_by_staff = (
            qs.values("staff__id", "staff__name",  "staff__email")
            .annotate(
                sales_count=Count("id"),
                units_sold=Sum("quantity"),
                revenue=Sum(
                    ExpressionWrapper(
                        F("quantity") * F("selling_price"),
                        output_field=DecimalField(max_digits=14, decimal_places=2),
                    )
                ),
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
                        "units_sold": row["units_sold"],
                    }
                    for row in trend
                ],
                "top_products": top_products,
                "sales_by_staff": [
                    {
                        "staff_id": str(row["staff__id"]),
                        "staff_name": (
                            f"{row['staff__first_name']} {row['staff__last_name']}".strip()
                            or row["staff__email"]
                        ),
                        "sales_count": row["sales_count"],
                        "units_sold": row["units_sold"],
                        "revenue": row["revenue"],
                    }
                    for row in sales_by_staff
                ],
            }
        )
