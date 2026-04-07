from rest_framework import status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from beyond_trend.core.viewsets import BaseModelViewSet

from beyond_trend.orders.models import Order, PreOrder
from beyond_trend.orders.api.filters import OrderFilter, PreOrderFilter
from beyond_trend.orders.api.serializers import (
    CreateOrderSerializer,
    OrderSerializer,
    PreOrderSerializer,
    UpdateOrderStatusSerializer,
)
from beyond_trend.orders.api.usecases import (
    CreateOrderUseCase,
    FulfillPreOrderUseCase,
    NotifyPreOrderUseCase,
    UpdateOrderStatusUseCase,
)


class OrderViewSet(BaseModelViewSet):
    serializer_class = OrderSerializer
    queryset = Order.objects.prefetch_related("items__variant__brand").all()
    permission_classes = [IsAuthenticated]
    filterset_class = OrderFilter
    search_fields = ["customer_name", "email", "phone"]
    ordering_fields = ["created_at", "total_amount", "status"]
    # Orders are immutable once created — only the status action can change them.
    http_method_names = ["get", "post", "head", "options"]

    def create(self, request, *args, **kwargs):
        serializer = CreateOrderSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        use_case = CreateOrderUseCase(
            data=serializer.validated_data,
            staff=request.user,
        )
        order = use_case.execute()
        return Response(
            OrderSerializer(order, context={"request": request}).data,
            status=status.HTTP_201_CREATED,
        )

    @action(detail=True, methods=["patch"], url_path="status")
    def update_status(self, request, pk=None):
        order = self.get_object()
        serializer = UpdateOrderStatusSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        use_case = UpdateOrderStatusUseCase(
            order=order,
            new_status=serializer.validated_data["status"],
            staff=request.user,
        )
        updated_order = use_case.execute()
        return Response(OrderSerializer(updated_order, context=self.get_serializer_context()).data)


class PreOrderViewSet(BaseModelViewSet):
    serializer_class = PreOrderSerializer
    queryset = PreOrder.objects.all()
    permission_classes = [IsAuthenticated]
    filterset_class = PreOrderFilter
    search_fields = ["customer_name", "email", "phone", "product_name", "brand"]
    ordering_fields = ["created_at", "status"]

    @action(detail=True, methods=["patch"], url_path="notify")
    def notify(self, request, pk=None):
        use_case = NotifyPreOrderUseCase(pre_order=self.get_object())
        return Response(use_case.execute())

    @action(detail=True, methods=["patch"], url_path="fulfill")
    def fulfill(self, request, pk=None):
        use_case = FulfillPreOrderUseCase(pre_order=self.get_object())
        return Response(use_case.execute())
