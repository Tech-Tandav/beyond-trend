from django.conf import settings
from django.urls import path
from rest_framework.routers import DefaultRouter, SimpleRouter

from beyond_trend.inventory.api.analytics import InventoryAnalyticsView
from beyond_trend.inventory.api.views import (
    BrandViewSet,
    CategoryViewSet,
    InventoryLogViewSet,
    ProductVariantViewSet,
    ProductViewSet,
    StockViewSet,
    ShoeProductViewSet
)

router = DefaultRouter() if settings.DEBUG else SimpleRouter()

router.register("brands", BrandViewSet)
router.register("categories", CategoryViewSet)
router.register("products", ProductViewSet)
router.register("variants", ProductVariantViewSet)
router.register("stocks", StockViewSet)
router.register("logs", InventoryLogViewSet)
router.register("shoe", ShoeProductViewSet)

app_name = "inventory"

urlpatterns = [
    path("analytics/", InventoryAnalyticsView.as_view(), name="inventory-analytics"),
]
urlpatterns += router.urls
