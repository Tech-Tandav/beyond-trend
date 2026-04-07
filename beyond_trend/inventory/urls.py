from django.conf import settings
from django.urls import path
from rest_framework.routers import DefaultRouter, SimpleRouter

from beyond_trend.inventory.api.analytics import InventoryAnalyticsView
from beyond_trend.inventory.api.views import (
    VendorViewSet,
    BrandViewSet,
    InventoryLogViewSet,
    ProductCheckInView,
    ProductCheckOutView,
    ProductCreateView,
    ProductDestroyView,
    ProductListView,
    ProductRetrieveView,
    ProductUpdateView,
    PublicInventoryView,
    StockViewSet,
)

router = DefaultRouter() if settings.DEBUG else SimpleRouter()


router.register("vendors", VendorViewSet)
router.register("brands", BrandViewSet)
router.register("stocks", StockViewSet)
router.register("logs", InventoryLogViewSet)

app_name = "inventory"

urlpatterns = [
    path("analytics/", InventoryAnalyticsView.as_view(), name="inventory-analytics"),
    path("public-inventory/", PublicInventoryView.as_view(), name="inventory-public"),
    path("products/", ProductListView.as_view(), name="product-list"),
    path("products/create/", ProductCreateView.as_view(), name="product-create"),
    path("products/check-in/", ProductCheckInView.as_view(), name="product-check-in"),
    path("products/check-out/", ProductCheckOutView.as_view(), name="product-check-out"),
    path("products/<slug:slug>/", ProductRetrieveView.as_view(), name="product-detail"),
    path("products/<slug:slug>/update/", ProductUpdateView.as_view(), name="product-update"),
    path("products/<slug:slug>/delete/", ProductDestroyView.as_view(), name="product-delete"),
]
urlpatterns += router.urls
