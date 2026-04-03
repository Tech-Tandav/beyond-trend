from rest_framework import status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from beyond_trend.core.viewsets import BaseModelViewSet

from ..models import Sale
from .serializers import CheckoutSerializer, SaleSerializer
from .usecases import CheckoutUseCase


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

        use_case = CheckoutUseCase(data=serializer.validated_data, staff=request.user)
        sale = use_case.execute()
        return Response(
            SaleSerializer(sale, context=self.get_serializer_context()).data,
            status=status.HTTP_201_CREATED,
        )
