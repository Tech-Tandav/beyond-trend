from django.conf import settings
from django.urls import path
from rest_framework.routers import DefaultRouter, SimpleRouter

from beyond_trend.inventory.api.analytics import InventoryAnalyticsView
from beyond_trend.inventory.api.views import (
    VendorViewSet,
    BrandViewSet,
    InventoryLogViewSet,
    ProductViewSet,
    StockViewSet,
)

router = DefaultRouter() if settings.DEBUG else SimpleRouter()


router.register("vendors", VendorViewSet)
router.register("brands", BrandViewSet)
router.register("products", ProductViewSet)
router.register("stocks", StockViewSet)
router.register("logs", InventoryLogViewSet)

app_name = "inventory"

urlpatterns = [
    path("analytics/", InventoryAnalyticsView.as_view(), name="inventory-analytics"),
]
urlpatterns += router.urls
