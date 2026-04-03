from rest_framework import status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from beyond_trend.core.viewsets import BaseModelViewSet

from beyond_trend.sales.models import Sale, ShoeSale
from beyond_trend.sales.api.filters import SaleFilter
from beyond_trend.sales.api.serializers import CheckoutSerializer, SaleSerializer, ShoeCheckoutSerializer, ShoeSaleSerializer, ShoeSaleSerializer
from beyond_trend.sales.api.usecases import CheckoutUseCase, ShoeCheckoutUseCase


class SaleViewSet(BaseModelViewSet):
    serializer_class = ShoeSaleSerializer
    queryset = ShoeSale.objects.all()
    permission_classes = [IsAuthenticated]
    # http_method_names = ["get", "head", "options", "post"]
    # filterset_class = SaleFilter
    # search_fields = ["customer__name", "customer__email", "staff__name"]
    # ordering_fields = ["created_at", "total_amount", "subtotal"]

    # @action(detail=False, methods=["post"], url_path="checkout")
    # def checkout(self, request):
    #     """
    #     POS Checkout:
    #     - Validates stock for all items
    #     - Creates Sale + SaleItems
    #     - Reduces stock
    #     - Logs inventory check-out
    #     - Awards / deducts loyalty points if customer selected
    #     """
    #     serializer = CheckoutSerializer(data=request.data)
    #     serializer.is_valid(raise_exception=True)

    #     use_case = CheckoutUseCase(data=serializer.validated_data, staff=request.user)
    #     sale = use_case.execute()
    #     return Response(
    #         SaleSerializer(sale, context=self.get_serializer_context()).data,
    #         status=status.HTTP_201_CREATED,
    #     )
        
    @action(detail=False, methods=["post"], url_path="shoe-checkout")
    def shoe_checkout(self, request):
        serializer = ShoeCheckoutSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        use_case = ShoeCheckoutUseCase(data=serializer.validated_data, staff=request.user)
        sale = use_case.execute()
        return Response(
            ShoeSaleSerializer(sale, context=self.get_serializer_context()).data,
            status=status.HTTP_201_CREATED,
        )