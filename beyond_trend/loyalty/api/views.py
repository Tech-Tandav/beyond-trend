from drf_spectacular.utils import extend_schema, extend_schema_view, OpenApiParameter, OpenApiResponse
from drf_spectacular.types import OpenApiTypes
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from beyond_trend.core.viewsets import BaseModelViewSet
from beyond_trend.loyalty.models import Customer, LoyaltyTransaction, LOYALTY_ELIGIBLE_SUBCATEGORY_SLUG
from beyond_trend.loyalty.api.filters import CustomerFilter, LoyaltyTransactionFilter
from beyond_trend.loyalty.api.serializers import (
    CustomerLookupSerializer,
    CustomerSerializer,
    EarnPointsSerializer,
    LoyaltyTransactionSerializer,
)
from beyond_trend.sales.models import Sale, SaleItem


@extend_schema_view(
    list=extend_schema(
        tags=["Loyalty"],
        summary="List customers",
        description="Returns a paginated list of loyalty customers.",
        parameters=[
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
    ordering_fields = ["created_at", "total_points"]

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
        description=(
            "Award 100 points for a sneaker purchase. Only sneaker category items "
            "are eligible. When customer reaches 500 points, a 10%% discount is "
            "applied on the current transaction and points reset."
        ),
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

            # Validate sale contains at least one sneaker item
            has_sneakers = SaleItem.objects.filter(
                sale=sale,
                product__subcategory__slug=LOYALTY_ELIGIBLE_SUBCATEGORY_SLUG,
            ).exists()
            if not has_sneakers:
                return Response(
                    {"detail": "No sneaker items in this sale. Points not awarded."},
                    status=status.HTTP_400_BAD_REQUEST,
                )

        points_earned, discount_percent = customer.earn_points()

        transaction = LoyaltyTransaction.objects.create(
            customer=customer,
            transaction_type=LoyaltyTransaction.EARN,
            points=points_earned,
            discount_applied=discount_percent,
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


@extend_schema_view(
    list=extend_schema(
        tags=["Loyalty"],
        summary="List loyalty transactions",
        description="Returns a paginated list of all loyalty point transactions.",
        parameters=[
            OpenApiParameter("customer", OpenApiTypes.UUID, OpenApiParameter.QUERY, description="Filter by customer UUID."),
            OpenApiParameter("transaction_type", OpenApiTypes.STR, OpenApiParameter.QUERY, description="Filter by type (earn)."),
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
