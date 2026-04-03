from django.conf import settings
from rest_framework.routers import DefaultRouter, SimpleRouter

from beyond_trend.sales.api.views import SaleViewSet

router = DefaultRouter() if settings.DEBUG else SimpleRouter()

router.register("sales", SaleViewSet)

app_name = "sales"

urlpatterns = router.urls
