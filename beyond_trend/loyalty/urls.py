from django.conf import settings
from rest_framework.routers import DefaultRouter, SimpleRouter

from beyond_trend.loyalty.api.views import CustomerViewSet, LoyaltyTransactionViewSet

router = DefaultRouter() if settings.DEBUG else SimpleRouter()

router.register("customers", CustomerViewSet)
router.register("transactions", LoyaltyTransactionViewSet)

app_name = "loyalty"

urlpatterns = router.urls
