from rest_framework.routers import DefaultRouter

from .views import CaseViewSet

router = DefaultRouter()
router.register(r"cases", CaseViewSet, basename="case")

app_name = "cases"
urlpatterns = router.urls
