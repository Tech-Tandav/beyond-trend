from django.db import transaction
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from beyond_trend.core.viewsets import BaseModelViewSet
from beyond_trend.inventory.models import ProductVariant
from beyond_trend.loyalty.models import Customer

from ..models import Order, OrderItem, PreOrder
from .serializers import (
    CreateOrderSerializer,
    OrderSerializer,
    PreOrderSerializer,
    UpdateOrderStatusSerializer,
)


class OrderViewSet(BaseModelViewSet):
    serializer_class = OrderSerializer
    queryset = Order.objects.prefetch_related("items").all()
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        qs = super().get_queryset()
        order_status = self.request.query_params.get("status")
        if order_status:
            qs = qs.filter(status=order_status)
        return qs

    def create(self, request, *args, **kwargs):
        return self._create_order(request)

    @transaction.atomic
    def _create_order(self, request):
        serializer = CreateOrderSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        loyalty_customer = None
        loyalty_customer_id = data.get("loyalty_customer_id")
        if loyalty_customer_id:
            try:
                loyalty_customer = Customer.objects.get(id=loyalty_customer_id)
            except Customer.DoesNotExist:
                return Response(
                    {"detail": "Loyalty customer not found."},
                    status=status.HTTP_404_NOT_FOUND,
                )

        total_amount = 0
        items_to_create = []
        for item in data["items"]:
            try:
                variant = ProductVariant.objects.get(id=item["variant_id"])
            except ProductVariant.DoesNotExist:
                return Response(
                    {"detail": f"Variant {item['variant_id']} not found."},
                    status=status.HTTP_404_NOT_FOUND,
                )
            price = variant.selling_price
            total_amount += price * item["quantity"]
            items_to_create.append((variant, item["quantity"], price))

        order = Order.objects.create(
            customer_name=data["customer_name"],
            email=data["email"],
            phone=data.get("phone", ""),
            notes=data.get("notes", ""),
            total_amount=total_amount,
            loyalty_customer=loyalty_customer,
        )

        for variant, quantity, price in items_to_create:
            OrderItem.objects.create(
                order=order,
                variant=variant,
                quantity=quantity,
                price=price,
            )

        return Response(
            OrderSerializer(order, context={"request": request}).data,
            status=status.HTTP_201_CREATED,
        )

    @action(detail=True, methods=["patch"], url_path="status")
    def update_status(self, request, pk=None):
        order = self.get_object()
        serializer = UpdateOrderStatusSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        order.status = serializer.validated_data["status"]
        order.save(update_fields=["status"])
        return Response(OrderSerializer(order, context=self.get_serializer_context()).data)


class PreOrderViewSet(BaseModelViewSet):
    serializer_class = PreOrderSerializer
    queryset = PreOrder.objects.all()
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        qs = super().get_queryset()
        order_status = self.request.query_params.get("status")
        if order_status:
            qs = qs.filter(status=order_status)
        return qs

    @action(detail=True, methods=["patch"], url_path="notify")
    def notify(self, request, pk=None):
        pre_order = self.get_object()
        pre_order.status = PreOrder.NOTIFIED
        pre_order.save(update_fields=["status"])
        return Response({"detail": "Customer marked as notified."})

    @action(detail=True, methods=["patch"], url_path="fulfill")
    def fulfill(self, request, pk=None):
        pre_order = self.get_object()
        pre_order.status = PreOrder.FULFILLED
        pre_order.save(update_fields=["status"])
        return Response({"detail": "Pre-order marked as fulfilled."})
