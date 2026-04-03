from django.conf import settings
from rest_framework.routers import DefaultRouter, SimpleRouter

from beyond_trend.orders.api.views import OrderViewSet, PreOrderViewSet

router = DefaultRouter() if settings.DEBUG else SimpleRouter()

router.register("orders", OrderViewSet)
router.register("pre-orders", PreOrderViewSet)

app_name = "orders"

urlpatterns = router.urls
