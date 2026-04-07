from django.conf import settings
from django.urls import path
from rest_framework.routers import DefaultRouter, SimpleRouter

from beyond_trend.orders.api.views import (
    OrderCreateAPIView,
    OrderListAPIView,
    OrderRetrieveAPIView,
    OrderStatusUpdateAPIView,
    PreOrderViewSet,
)

router = DefaultRouter() if settings.DEBUG else SimpleRouter()

router.register("pre-orders", PreOrderViewSet)

app_name = "orders"

urlpatterns = [
    path("orders/", OrderListAPIView.as_view(), name="order-list"),
    path("orders/create/", OrderCreateAPIView.as_view(), name="order-create"),
    path("orders/<uuid:pk>/", OrderRetrieveAPIView.as_view(), name="order-detail"),
    path(
        "orders/<uuid:pk>/status/",
        OrderStatusUpdateAPIView.as_view(),
        name="order-status",
    ),
    *router.urls,
]
