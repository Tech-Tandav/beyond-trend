from drf_spectacular.utils import (
    OpenApiExample,
    OpenApiResponse,
    extend_schema,
    extend_schema_view,
)
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


@extend_schema(
    tags=["Orders"],
    summary="List orders",
    description=(
        "Returns a paginated list of customer orders.\n\n"
        "Supports filtering via `OrderFilter`, `?search=` on customer name / email / phone, "
        "and `?ordering=` on `created_at`, `total_amount`, `status`."
    ),
)
class OrderListAPIView(generics.ListAPIView):
    serializer_class = OrderSerializer
    queryset = Order.objects.prefetch_related("items__product__brand").all()
    permission_classes = [IsAuthenticated]
    filterset_class = OrderFilter
    search_fields = ["customer_name", "email", "phone"]
    ordering_fields = ["created_at", "total_amount", "status"]


@extend_schema(
    tags=["Orders"],
    summary="Get an order",
    description="Retrieve a single order with its line items.",
)
class OrderRetrieveAPIView(generics.RetrieveAPIView):
    serializer_class = OrderSerializer
    queryset = Order.objects.prefetch_related("items__product__brand").all()
    permission_classes = [IsAuthenticated]


@extend_schema(
    tags=["Orders"],
    summary="Create an order",
    description=(
        "Public endpoint used by the storefront checkout. Creates a new order with the "
        "supplied items, computes `total_amount` from current product prices, and (if "
        "`loyalty_customer_id` is supplied) links the order to a loyalty customer.\n\n"
        "Returns the full order including line items."
    ),
    request=CreateOrderSerializer,
    responses={201: OrderSerializer},
    examples=[
        OpenApiExample(
            "Guest checkout",
            value={
                "customer_name": "Asha Shrestha",
                "email": "asha@example.com",
                "phone": "+9779812345678",
                "items": [
                    {"product_id": "0d3b3ce6-1b9f-4f1d-8f5d-6f1a2c2d3e4f", "quantity": 1},
                ],
                "notes": "Please gift wrap.",
            },
            request_only=True,
        ),
    ],
)
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


@extend_schema(
    tags=["Orders"],
    summary="Update order status",
    description=(
        "Transitions an order to a new status (e.g. `pending` → `confirmed` → `shipped` → "
        "`delivered`, or `cancelled`). The use-case enforces valid transitions and "
        "automatically restocks items on cancellation."
    ),
    request=UpdateOrderStatusSerializer,
    responses={200: OrderSerializer, 404: OpenApiResponse(description="Order not found.")},
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


@extend_schema_view(
    list=extend_schema(
        tags=["Pre-Orders"],
        summary="List pre-orders",
        description="Pre-orders are customer requests for items not currently in stock.",
    ),
    retrieve=extend_schema(tags=["Pre-Orders"], summary="Get a pre-order"),
    create=extend_schema(tags=["Pre-Orders"], summary="Create a pre-order"),
    update=extend_schema(tags=["Pre-Orders"], summary="Replace a pre-order"),
    partial_update=extend_schema(tags=["Pre-Orders"], summary="Patch a pre-order"),
    destroy=extend_schema(tags=["Pre-Orders"], summary="Delete a pre-order"),
)
class PreOrderViewSet(BaseModelViewSet):
    serializer_class = PreOrderSerializer
    queryset = PreOrder.objects.all()
    permission_classes = [IsAuthenticated]
    filterset_class = PreOrderFilter
    search_fields = ["customer_name", "email", "phone", "product_name", "brand"]
    ordering_fields = ["created_at", "status"]

    @extend_schema(
        tags=["Pre-Orders"],
        summary="Notify customer",
        description="Marks the pre-order as notified and sends an email to the customer that the requested item is now available.",
        request=None,
        responses={200: OpenApiResponse(description="Notification dispatched.")},
    )
    @action(detail=True, methods=["patch"], url_path="notify")
    def notify(self, request, pk=None):
        use_case = NotifyPreOrderUseCase(pre_order=self.get_object())
        return Response(use_case.execute())

    @extend_schema(
        tags=["Pre-Orders"],
        summary="Fulfill pre-order",
        description="Marks the pre-order as fulfilled (the customer has picked up or purchased the item).",
        request=None,
        responses={200: OpenApiResponse(description="Pre-order marked fulfilled.")},
    )
    @action(detail=True, methods=["patch"], url_path="fulfill")
    def fulfill(self, request, pk=None):
        use_case = FulfillPreOrderUseCase(pre_order=self.get_object())
        return Response(use_case.execute())
