from django.db.models import Count, DecimalField, ExpressionWrapper, F, Sum
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from beyond_trend.inventory.models import Product


class InventoryAnalyticsView(APIView):
    """
    GET /api/v1/inventory/analytics/

    Returns a snapshot of the current inventory state for ShoeProduct.
    No date filtering — stock levels are always current.
    """

    permission_classes = [IsAuthenticated]

    def get(self, request):
        qs = Product.objects.all()

        stock_value_expr = ExpressionWrapper(
            F("selling_price") * F("quantity"),
            output_field=DecimalField(max_digits=14, decimal_places=2),
        )

        # --- Summary ---
        agg = qs.annotate(stock_value=stock_value_expr).aggregate(
            total_products=Count("id"),
            total_units=Sum("quantity"),
            total_stock_value=Sum("stock_value"),
        )

        total_products = agg["total_products"] or 0
        total_units = agg["total_units"] or 0
        total_stock_value = agg["total_stock_value"] or 0

        low_stock_count = qs.filter(quantity__gt=0, quantity__lte=5).count()
        out_of_stock_count = qs.filter(quantity=0).count()

        # --- Stock by brand ---
        stock_by_brand = (
            qs.annotate(stock_value=stock_value_expr)
            .values("brand_name")
            .annotate(
                products=Count("id"),
                units=Sum("quantity"),
                stock_value=Sum(stock_value_expr),
            )
            .order_by("-stock_value")
        )

        # --- Top stocked products ---
        top_stocked = (
            qs.annotate(stock_value=stock_value_expr)
            .values("barcode", "brand_name", "size", "color", "quantity", "selling_price", "stock_value")
            .order_by("-quantity")[:10]
        )

        # --- Low stock items (quantity 1–5) ---
        low_stock_items = qs.filter(quantity__gt=0, quantity__lte=5).values(
            "barcode", "brand_name", "size", "color", "quantity", "selling_price"
        ).order_by("quantity")

        # --- Out of stock items ---
        out_of_stock_items = qs.filter(quantity=0).values(
            "barcode", "brand_name", "size", "color", "selling_price"
        )

        return Response(
            {
                "summary": {
                    "total_products": total_products,
                    "total_units": total_units,
                    "total_stock_value": total_stock_value,
                    "low_stock_count": low_stock_count,
                    "out_of_stock_count": out_of_stock_count,
                },
                "stock_by_brand": [
                    {
                        "brand_name": row["brand_name"],
                        "products": row["products"],
                        "units": row["units"],
                        "stock_value": row["stock_value"],
                    }
                    for row in stock_by_brand
                ],
                "top_stocked_products": [
                    {
                        "barcode": row["barcode"],
                        "brand_name": row["brand_name"],
                        "size": row["size"],
                        "color": row["color"],
                        "quantity": row["quantity"],
                        "selling_price": row["selling_price"],
                        "stock_value": row["stock_value"],
                    }
                    for row in top_stocked
                ],
                "low_stock_items": list(low_stock_items),
                "out_of_stock_items": list(out_of_stock_items),
            }
        )
