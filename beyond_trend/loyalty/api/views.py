from drf_spectacular.utils import extend_schema, extend_schema_view, OpenApiParameter, OpenApiResponse
from drf_spectacular.types import OpenApiTypes
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from beyond_trend.core.viewsets import BaseModelViewSet
from beyond_trend.loyalty.models import Customer, LoyaltyTransaction
from beyond_trend.loyalty.api.filters import CustomerFilter, LoyaltyTransactionFilter
from beyond_trend.loyalty.api.serializers import (
    CustomerLookupSerializer,
    CustomerSerializer,
    EarnPointsSerializer,
    LoyaltyTransactionSerializer,
    RedeemPointsSerializer,
)
from beyond_trend.sales.models import Sale


@extend_schema_view(
    list=extend_schema(
        tags=["Loyalty"],
        summary="List customers",
        description="Returns a paginated list of loyalty customers.",
        parameters=[
            OpenApiParameter("tier", OpenApiTypes.STR, OpenApiParameter.QUERY, description="Filter by tier (bronze, silver, gold, platinum)."),
            OpenApiParameter("phone", OpenApiTypes.STR, OpenApiParameter.QUERY, description="Search by phone number (partial match)."),
            OpenApiParameter("search", OpenApiTypes.STR, OpenApiParameter.QUERY, description="Search by name, phone, or email."),
        ],
    ),
    retrieve=extend_schema(tags=["Loyalty"], summary="Get customer details"),
    create=extend_schema(tags=["Loyalty"], summary="Register a new loyalty customer"),
    update=extend_schema(tags=["Loyalty"], summary="Update customer info"),
    partial_update=extend_schema(tags=["Loyalty"], summary="Partially update customer info"),
)
class CustomerViewSet(BaseModelViewSet):
    serializer_class = CustomerSerializer
    queryset = Customer.objects.all()
    permission_classes = [IsAuthenticated]
    filterset_class = CustomerFilter
    search_fields = ["name", "phone", "email"]
    ordering_fields = ["created_at", "total_spend", "total_points", "tier"]

    @extend_schema(
        tags=["Loyalty"],
        summary="Look up customer by phone",
        description="Find a customer by their phone number. Returns 404 if not found.",
        request=CustomerLookupSerializer,
        responses={200: CustomerSerializer, 404: OpenApiResponse(description="Customer not found.")},
    )
    @action(detail=False, methods=["post"], url_path="lookup")
    def lookup(self, request):
        serializer = CustomerLookupSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            customer = Customer.objects.get(phone=serializer.validated_data["phone"])
        except Customer.DoesNotExist:
            return Response(
                {"detail": "Customer not found."},
                status=status.HTTP_404_NOT_FOUND,
            )
        return Response(
            CustomerSerializer(customer, context=self.get_serializer_context()).data
        )

    @extend_schema(
        tags=["Loyalty"],
        summary="Earn loyalty points",
        description="Award points to a customer based on purchase amount. 1 point per NPR 100 spent.",
        request=EarnPointsSerializer,
        responses={200: LoyaltyTransactionSerializer},
    )
    @action(detail=False, methods=["post"], url_path="earn")
    def earn_points(self, request):
        serializer = EarnPointsSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        try:
            customer = Customer.objects.get(id=data["customer_id"])
        except Customer.DoesNotExist:
            return Response(
                {"detail": "Customer not found."},
                status=status.HTTP_404_NOT_FOUND,
            )

        sale = None
        if data.get("sale_id"):
            try:
                sale = Sale.objects.get(id=data["sale_id"])
            except Sale.DoesNotExist:
                return Response(
                    {"detail": "Sale not found."},
                    status=status.HTTP_404_NOT_FOUND,
                )

        points = customer.earn_points(data["amount"])

        transaction = LoyaltyTransaction.objects.create(
            customer=customer,
            transaction_type=LoyaltyTransaction.EARN,
            points=points,
            sale=sale,
            staff=request.user,
            notes=data.get("notes", ""),
        )

        return Response(
            LoyaltyTransactionSerializer(
                transaction, context=self.get_serializer_context()
            ).data,
            status=status.HTTP_200_OK,
        )

    @extend_schema(
        tags=["Loyalty"],
        summary="Redeem loyalty points",
        description="Redeem points from a customer's balance. 1 point = NPR 1 discount.",
        request=RedeemPointsSerializer,
        responses={
            200: LoyaltyTransactionSerializer,
            400: OpenApiResponse(description="Insufficient points."),
        },
    )
    @action(detail=False, methods=["post"], url_path="redeem")
    def redeem_points(self, request):
        serializer = RedeemPointsSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        try:
            customer = Customer.objects.get(id=data["customer_id"])
        except Customer.DoesNotExist:
            return Response(
                {"detail": "Customer not found."},
                status=status.HTTP_404_NOT_FOUND,
            )

        if not customer.redeem_points(data["points"]):
            return Response(
                {
                    "detail": f"Insufficient points. Available: {customer.available_points}"
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        transaction = LoyaltyTransaction.objects.create(
            customer=customer,
            transaction_type=LoyaltyTransaction.REDEEM,
            points=-data["points"],
            staff=request.user,
            notes=data.get("notes", ""),
        )

        return Response(
            LoyaltyTransactionSerializer(
                transaction, context=self.get_serializer_context()
            ).data,
            status=status.HTTP_200_OK,
        )


@extend_schema_view(
    list=extend_schema(
        tags=["Loyalty"],
        summary="List loyalty transactions",
        description="Returns a paginated list of all loyalty point transactions.",
        parameters=[
            OpenApiParameter("customer", OpenApiTypes.UUID, OpenApiParameter.QUERY, description="Filter by customer UUID."),
            OpenApiParameter("transaction_type", OpenApiTypes.STR, OpenApiParameter.QUERY, description="Filter by type (earn, redeem, adjustment)."),
            OpenApiParameter("date_from", OpenApiTypes.DATE, OpenApiParameter.QUERY),
            OpenApiParameter("date_to", OpenApiTypes.DATE, OpenApiParameter.QUERY),
        ],
    ),
    retrieve=extend_schema(tags=["Loyalty"], summary="Get transaction details"),
)
class LoyaltyTransactionViewSet(BaseModelViewSet):
    serializer_class = LoyaltyTransactionSerializer
    queryset = LoyaltyTransaction.objects.all()
    permission_classes = [IsAuthenticated]
    http_method_names = ["get", "head", "options"]
    filterset_class = LoyaltyTransactionFilter
    search_fields = ["customer__name", "customer__phone"]
    ordering_fields = ["created_at", "points"]
