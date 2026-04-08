from django.db import models
from django.db.models import Count, Sum, Value
from django.db.models.functions import Coalesce
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import (
    OpenApiExample,
    OpenApiParameter,
    OpenApiResponse,
    extend_schema,
    extend_schema_view,
    inline_serializer,
)
from rest_framework import serializers, status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from beyond_trend.core.viewsets import BaseModelViewSet

from beyond_trend.loyalty.models import Customer, LoyaltySettings, LoyaltyTransaction
from beyond_trend.loyalty.api.filters import CustomerFilter, LoyaltyTransactionFilter
from beyond_trend.loyalty.api.serializers import (
    CustomerSerializer,
    LoyaltySettingsSerializer,
    LoyaltyTransactionSerializer,
    RedeemPointsSerializer,
)
from beyond_trend.loyalty.api.usecases import RedeemPointsUseCase


RedeemResponseSerializer = inline_serializer(
    name="RedeemPointsResponse",
    fields={
        "detail": serializers.CharField(),
        "customer_id": serializers.UUIDField(),
        "points_redeemed": serializers.IntegerField(),
        "remaining_points": serializers.IntegerField(),
    },
)


@extend_schema_view(
    list=extend_schema(
        tags=["Loyalty - Customers"],
        summary="List loyalty customers",
        description="Paginated list of loyalty customers. Supports `?search=` on name / email / phone and ordering by `name`, `total_points`, `created_at`.",
        parameters=[
            OpenApiParameter("email", OpenApiTypes.STR, OpenApiParameter.QUERY, description="Filter by exact email."),
            OpenApiParameter("email__icontains", OpenApiTypes.STR, OpenApiParameter.QUERY, description="Filter by email (case-insensitive contains)."),
            OpenApiParameter("phone", OpenApiTypes.STR, OpenApiParameter.QUERY, description="Filter by exact phone."),
            OpenApiParameter("phone__icontains", OpenApiTypes.STR, OpenApiParameter.QUERY, description="Filter by phone (case-insensitive contains)."),
            OpenApiParameter("search", OpenApiTypes.STR, OpenApiParameter.QUERY, description="Search across name, email, phone."),
            OpenApiParameter("ordering", OpenApiTypes.STR, OpenApiParameter.QUERY, description="Order by: name, total_points, created_at (prefix `-` for descending)."),
        ],
    ),
    retrieve=extend_schema(tags=["Loyalty - Customers"], summary="Get a customer"),
    create=extend_schema(tags=["Loyalty - Customers"], summary="Create a customer"),
    update=extend_schema(tags=["Loyalty - Customers"], summary="Replace a customer"),
    partial_update=extend_schema(tags=["Loyalty - Customers"], summary="Patch a customer"),
    destroy=extend_schema(tags=["Loyalty - Customers"], summary="Archive a customer"),
)
class CustomerViewSet(BaseModelViewSet):
    serializer_class = CustomerSerializer
    queryset = Customer.objects.annotate(
        transaction_count=Count("sales", distinct=True),
        transaction_amount=Coalesce(Sum("sales__total_amount"), Value(0), output_field=models.DecimalField(max_digits=12, decimal_places=2)),
    )
    permission_classes = [IsAuthenticated]
    filterset_class = CustomerFilter
    search_fields = ["name", "email", "phone"]
    ordering_fields = ["name", "total_points", "created_at", "transaction_count", "transaction_amount"]

    @extend_schema(
        tags=["Loyalty - Customers"],
        summary="List a customer's transactions",
        description="Returns the full loyalty point ledger for the given customer.",
        responses={200: LoyaltyTransactionSerializer(many=True)},
    )
    @action(detail=True, methods=["get"], url_path="transactions")
    def transactions(self, request, pk=None):
        customer = self.get_object()
        txns = LoyaltyTransaction.objects.filter(customer=customer)
        serializer = LoyaltyTransactionSerializer(txns, many=True, context=self.get_serializer_context())
        return Response(serializer.data)

    @extend_schema(
        tags=["Loyalty - Customers"],
        summary="Redeem loyalty points",
        description=(
            "Deducts `points` from the customer's `total_points` and writes a "
            "`LoyaltyTransaction` of type `REDEEM`. Returns `400` if the customer does "
            "not have enough points to redeem."
        ),
        request=RedeemPointsSerializer,
        responses={
            200: RedeemResponseSerializer,
            400: OpenApiResponse(description="Insufficient points."),
            404: OpenApiResponse(description="Customer not found."),
        },
        examples=[
            OpenApiExample(
                "Redeem 100 points",
                value={
                    "customer_id": "11111111-2222-3333-4444-555555555555",
                    "points": 100,
                    "notes": "Birthday discount",
                },
                request_only=True,
            ),
        ],
    )
    @action(detail=False, methods=["post"], url_path="redeem")
    def redeem(self, request):
        """Redeem loyalty points for a customer."""
        serializer = RedeemPointsSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        use_case = RedeemPointsUseCase(
            customer_id=data["customer_id"],
            points=data["points"],
            notes=data.get("notes", ""),
        )
        return Response(use_case.execute(), status=status.HTTP_200_OK)


@extend_schema_view(
    list=extend_schema(
        tags=["Loyalty - Transactions"],
        summary="List loyalty transactions",
        description="Read-only ledger of every point movement (`EARN`, `REDEEM`, `ADJUST`).",
        parameters=[
            OpenApiParameter("customer", OpenApiTypes.UUID, OpenApiParameter.QUERY, description="Filter by loyalty customer UUID."),
            OpenApiParameter(
                "type",
                OpenApiTypes.STR,
                OpenApiParameter.QUERY,
                description="Filter by transaction type.",
                enum=[choice[0] for choice in LoyaltyTransaction.TYPE_CHOICES],
            ),
            OpenApiParameter("date_from", OpenApiTypes.DATE, OpenApiParameter.QUERY, description="Filter transactions on or after this date (YYYY-MM-DD)."),
            OpenApiParameter("date_to", OpenApiTypes.DATE, OpenApiParameter.QUERY, description="Filter transactions on or before this date (YYYY-MM-DD)."),
            OpenApiParameter("ordering", OpenApiTypes.STR, OpenApiParameter.QUERY, description="Order by: created_at, points, type (prefix `-` for descending)."),
        ],
    ),
    retrieve=extend_schema(tags=["Loyalty - Transactions"], summary="Get a transaction"),
)
class LoyaltyTransactionViewSet(BaseModelViewSet):
    serializer_class = LoyaltyTransactionSerializer
    queryset = LoyaltyTransaction.objects.select_related("customer", "sale").all()
    permission_classes = [IsAuthenticated]
    http_method_names = ["get", "head", "options"]
    filterset_class = LoyaltyTransactionFilter
    ordering_fields = ["created_at", "points", "type"]


@extend_schema_view(
    list=extend_schema(
        tags=["Loyalty - Settings"],
        summary="List loyalty settings",
        description="Loyalty settings are a singleton — this list always contains zero or one row. Prefer `/settings/current/`.",
    ),
    retrieve=extend_schema(tags=["Loyalty - Settings"], summary="Get loyalty settings"),
    partial_update=extend_schema(
        tags=["Loyalty - Settings"],
        summary="Update loyalty settings",
        description="Update the points-per-100-NPR ratio or the per-point NPR value.",
    ),
)
class LoyaltySettingsViewSet(BaseModelViewSet):
    serializer_class = LoyaltySettingsSerializer
    queryset = LoyaltySettings.objects.all()
    permission_classes = [IsAuthenticated]
    http_method_names = ["get", "patch", "head", "options"]

    def get_object(self):
        obj, _ = LoyaltySettings.objects.get_or_create(
            id=LoyaltySettings.objects.first().id
            if LoyaltySettings.objects.exists()
            else None
        )
        self.check_object_permissions(self.request, obj)
        return obj

    @extend_schema(
        tags=["Loyalty - Settings"],
        summary="Get current loyalty settings",
        description="Returns the active singleton `LoyaltySettings` row.",
        responses={
            200: LoyaltySettingsSerializer,
            404: OpenApiResponse(description="Loyalty settings not configured."),
        },
    )
    @action(detail=False, methods=["get"], url_path="current")
    def current(self, request):
        """Get the current loyalty settings (singleton)."""
        if not LoyaltySettings.objects.exists():
            return Response({"detail": "Loyalty settings not configured."}, status=status.HTTP_404_NOT_FOUND)
        obj = LoyaltySettings.objects.first()
        serializer = self.get_serializer(obj)
        return Response(serializer.data)
