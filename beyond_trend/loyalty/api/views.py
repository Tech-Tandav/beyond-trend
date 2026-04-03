from rest_framework import status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from beyond_trend.core.viewsets import BaseModelViewSet

from ..models import Customer, LoyaltySettings, LoyaltyTransaction
from .serializers import (
    CustomerSerializer,
    LoyaltySettingsSerializer,
    LoyaltyTransactionSerializer,
    RedeemPointsSerializer,
)
from .usecases import RedeemPointsUseCase


class CustomerViewSet(BaseModelViewSet):
    serializer_class = CustomerSerializer
    queryset = Customer.objects.all()
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        qs = super().get_queryset()
        search = self.request.query_params.get("search")
        if search:
            qs = qs.filter(name__icontains=search) | qs.filter(email__icontains=search) | qs.filter(phone__icontains=search)
        return qs

    @action(detail=True, methods=["get"], url_path="transactions")
    def transactions(self, request, pk=None):
        customer = self.get_object()
        txns = LoyaltyTransaction.objects.filter(customer=customer)
        serializer = LoyaltyTransactionSerializer(txns, many=True, context=self.get_serializer_context())
        return Response(serializer.data)

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


class LoyaltyTransactionViewSet(BaseModelViewSet):
    serializer_class = LoyaltyTransactionSerializer
    queryset = LoyaltyTransaction.objects.select_related("customer", "sale").all()
    permission_classes = [IsAuthenticated]
    http_method_names = ["get", "head", "options"]  # transactions are read-only via API


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

    @action(detail=False, methods=["get"], url_path="current")
    def current(self, request):
        """Get the current loyalty settings (singleton)."""
        if not LoyaltySettings.objects.exists():
            return Response({"detail": "Loyalty settings not configured."}, status=status.HTTP_404_NOT_FOUND)
        obj = LoyaltySettings.objects.first()
        serializer = self.get_serializer(obj)
        return Response(serializer.data)
