from rest_framework import generics, status
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

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


class OrderListAPIView(generics.ListAPIView):
    serializer_class = OrderSerializer
    queryset = Order.objects.prefetch_related("items__product__brand").all()
    permission_classes = [IsAuthenticated]
    filterset_class = OrderFilter
    search_fields = ["customer_name", "email", "phone"]
    ordering_fields = ["created_at", "total_amount", "status"]


class OrderRetrieveAPIView(generics.RetrieveAPIView):
    serializer_class = OrderSerializer
    queryset = Order.objects.prefetch_related("items__product__brand").all()
    permission_classes = [IsAuthenticated]


class OrderCreateAPIView(generics.CreateAPIView):
    serializer_class = CreateOrderSerializer
    permission_classes = [AllowAny]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
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


class OrderStatusUpdateAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def patch(self, request, pk):
        order = generics.get_object_or_404(Order, pk=pk)
        serializer = UpdateOrderStatusSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        use_case = UpdateOrderStatusUseCase(
            order=order,
            new_status=serializer.validated_data["status"],
            staff=request.user,
        )
        updated_order = use_case.execute()
        return Response(
            OrderSerializer(updated_order, context={"request": request}).data
        )


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
