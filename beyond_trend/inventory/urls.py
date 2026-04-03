from django.conf import settings
from rest_framework.routers import DefaultRouter, SimpleRouter

from beyond_trend.inventory.api.views import (
    BrandViewSet,
    CategoryViewSet,
    InventoryLogViewSet,
    ProductVariantViewSet,
    ProductViewSet,
    StockViewSet,
)

router = DefaultRouter() if settings.DEBUG else SimpleRouter()

router.register("brands", BrandViewSet)
router.register("categories", CategoryViewSet)
router.register("products", ProductViewSet)
router.register("variants", ProductVariantViewSet)
router.register("stocks", StockViewSet)
router.register("logs", InventoryLogViewSet)

app_name = "inventory"

urlpatterns = router.urls
