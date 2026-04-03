from django.conf import settings
from django.urls import path
from rest_framework.routers import DefaultRouter, SimpleRouter

from beyond_trend.sales.api.analytics import SalesAnalyticsView
from beyond_trend.sales.api.views import SaleViewSet

router = DefaultRouter() if settings.DEBUG else SimpleRouter()

router.register("sales", SaleViewSet)

app_name = "sales"

urlpatterns = [
    path("analytics/", SalesAnalyticsView.as_view(), name="sales-analytics"),
]
urlpatterns += router.urls
