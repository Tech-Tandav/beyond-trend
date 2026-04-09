from django.conf import settings
from django.urls import path
from rest_framework.routers import DefaultRouter, SimpleRouter

from beyond_trend.inventory.api.analytics import InventoryAnalyticsView
from beyond_trend.inventory.api.views import (
    BrandViewSet,
    CategoryViewSet,
    InventoryLogViewSet,
    ProductCheckInView,
    ProductCheckOutView,
    ProductCreateView,
    ProductDestroyView,
    ProductExcelExportAPIView,
    ProductListView,
    ProductRetrieveView,
    ProductUpdateView,
    PublicInventoryView,
    SizeListView,
    SubCategoryViewSet,
    VendorViewSet,
)

router = DefaultRouter() if settings.DEBUG else SimpleRouter()


router.register("vendors", VendorViewSet)
router.register("brands", BrandViewSet)
router.register("categories", CategoryViewSet)
router.register("subcategories", SubCategoryViewSet)
router.register("logs", InventoryLogViewSet)

app_name = "inventory"

urlpatterns = [
    path("analytics/", InventoryAnalyticsView.as_view(), name="inventory-analytics"),
    path("public-inventory/", PublicInventoryView.as_view(), name="inventory-public"),
    path("sizes/", SizeListView.as_view(), name="size-list"),
    path("products/", ProductListView.as_view(), name="product-list"),
    path("products/create/", ProductCreateView.as_view(), name="product-create"),
    path("products/export/", ProductExcelExportAPIView.as_view(), name="product-export"),
    path("products/check-in/", ProductCheckInView.as_view(), name="product-check-in"),
    path("products/check-out/", ProductCheckOutView.as_view(), name="product-check-out"),
    path("products/<str:barcode>/", ProductRetrieveView.as_view(), name="product-detail"),
    path("products/<slug:slug>/update/", ProductUpdateView.as_view(), name="product-update"),
    path("products/<slug:slug>/delete/", ProductDestroyView.as_view(), name="product-delete"),
]
urlpatterns += router.urls
