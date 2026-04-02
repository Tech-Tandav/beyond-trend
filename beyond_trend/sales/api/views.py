from django.db import transaction
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from beyond_trend.core.viewsets import BaseModelViewSet
from beyond_trend.inventory.models import InventoryLog, ProductVariant, Stock
from beyond_trend.loyalty.models import Customer, LoyaltySettings, LoyaltyTransaction

from ..models import Sale, SaleItem
from .serializers import CheckoutSerializer, SaleSerializer


class SaleViewSet(BaseModelViewSet):
    serializer_class = SaleSerializer
    queryset = Sale.objects.select_related("staff", "customer").prefetch_related("items").all()
    permission_classes = [IsAuthenticated]
    http_method_names = ["get", "head", "options", "post"]  # sales cannot be edited/deleted

    def get_queryset(self):
        qs = super().get_queryset()
        customer_id = self.request.query_params.get("customer")
        staff_id = self.request.query_params.get("staff")
        date_from = self.request.query_params.get("date_from")
        date_to = self.request.query_params.get("date_to")
        if customer_id:
            qs = qs.filter(customer__id=customer_id)
        if staff_id:
            qs = qs.filter(staff__id=staff_id)
        if date_from:
            qs = qs.filter(created_at__date__gte=date_from)
        if date_to:
            qs = qs.filter(created_at__date__lte=date_to)
        return qs

    @action(detail=False, methods=["post"], url_path="checkout")
    @transaction.atomic
    def checkout(self, request):
        """
        POS Checkout:
        - Validates stock for all items
        - Creates Sale + SaleItems
        - Reduces stock
        - Logs inventory check-out
        - Awards / deducts loyalty points if customer selected
        """
        serializer = CheckoutSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        customer = None
        customer_id = data.get("customer_id")
        if customer_id:
            try:
                customer = Customer.objects.get(id=customer_id)
            except Customer.DoesNotExist:
                return Response({"detail": "Customer not found."}, status=status.HTTP_404_NOT_FOUND)

        # Validate stock availability for all items first
        items_data = data["items"]
        variants = {}
        stocks = {}
        for item in items_data:
            vid = item["variant_id"]
            try:
                variant = ProductVariant.objects.get(id=vid)
            except ProductVariant.DoesNotExist:
                return Response(
                    {"detail": f"Variant {vid} not found."},
                    status=status.HTTP_404_NOT_FOUND,
                )
            try:
                stock = Stock.objects.get(variant=variant)
            except Stock.DoesNotExist:
                return Response(
                    {"detail": f"No stock for variant: {variant}"},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            if stock.quantity < item["quantity"]:
                return Response(
                    {
                        "detail": f"Insufficient stock for {variant}. "
                        f"Available: {stock.quantity}, Requested: {item['quantity']}"
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )
            variants[str(vid)] = variant
            stocks[str(vid)] = stock

        # Calculate totals
        subtotal = sum(
            item["quantity"] * item["selling_price"] for item in items_data
        )

        loyalty_points_used = data.get("loyalty_points_used", 0)
        discount_amount = 0

        if loyalty_points_used > 0 and customer:
            loyalty_settings = LoyaltySettings.objects.first()
            if not loyalty_settings:
                return Response(
                    {"detail": "Loyalty settings not configured."},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            if customer.total_points < loyalty_points_used:
                return Response(
                    {"detail": f"Insufficient loyalty points. Available: {customer.total_points}"},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            discount_amount = loyalty_points_used * loyalty_settings.point_value_npr

        total_amount = subtotal - discount_amount

        # Create Sale
        sale = Sale.objects.create(
            staff=request.user,
            customer=customer,
            subtotal=subtotal,
            discount_amount=discount_amount,
            total_amount=total_amount,
            loyalty_points_used=loyalty_points_used,
            notes=data.get("notes", ""),
        )

        # Create SaleItems, reduce stock, log inventory
        for item in items_data:
            vid = str(item["variant_id"])
            variant = variants[vid]
            stock = stocks[vid]

            SaleItem.objects.create(
                sale=sale,
                variant=variant,
                quantity=item["quantity"],
                selling_price=item["selling_price"],
            )

            stock.quantity -= item["quantity"]
            stock.save(update_fields=["quantity"])

            InventoryLog.objects.create(
                variant=variant,
                action=InventoryLog.CHECK_OUT,
                quantity=-item["quantity"],
                staff=request.user,
                notes=f"Sale #{str(sale.id)[:8]}",
            )

        # Handle loyalty points
        if customer:
            loyalty_settings = LoyaltySettings.objects.first()
            points_earned = 0
            if loyalty_settings:
                points_earned = int(float(total_amount) / 100 * loyalty_settings.points_per_100_npr)

            # Deduct redeemed points
            if loyalty_points_used > 0:
                customer.total_points -= loyalty_points_used
                LoyaltyTransaction.objects.create(
                    customer=customer,
                    points=-loyalty_points_used,
                    type=LoyaltyTransaction.REDEEMED,
                    sale=sale,
                    notes="Points redeemed at checkout",
                )

            # Award earned points
            if points_earned > 0:
                customer.total_points += points_earned
                LoyaltyTransaction.objects.create(
                    customer=customer,
                    points=points_earned,
                    type=LoyaltyTransaction.EARNED,
                    sale=sale,
                    notes="Points earned from purchase",
                )

            customer.save(update_fields=["total_points"])
            sale.loyalty_points_earned = points_earned
            sale.save(update_fields=["loyalty_points_earned"])

        return Response(
            SaleSerializer(sale, context=self.get_serializer_context()).data,
            status=status.HTTP_201_CREATED,
        )
