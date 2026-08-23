"""Root URL configuration."""

from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path, re_path
from drf_spectacular.views import (
    SpectacularAPIView,
    SpectacularRedocView,
    SpectacularSwaggerView,
)

from apps.core.views import SPAFallbackView

api_v1_patterns = [
    path("", include("apps.core.urls")),
    path("auth/", include("apps.accounts.urls")),
    path("", include("apps.cases.urls")),
    path("", include("apps.cea.urls")),
    path("", include("apps.econ.urls")),
    path("", include("apps.bia.urls")),
    path("", include("apps.etd.urls")),
    path("", include("apps.recommendation.urls")),
    path("", include("apps.approval.urls")),
    path("", include("apps.policy_brief.urls")),
    path("", include("apps.versioning.urls")),
    path("", include("apps.archive.urls")),
]

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/v1/", include(api_v1_patterns)),
    path("api/schema/", SpectacularAPIView.as_view(), name="schema"),
    path("api/schema/swagger/", SpectacularSwaggerView.as_view(url_name="schema"), name="swagger"),
    path("api/schema/redoc/", SpectacularRedocView.as_view(url_name="schema"), name="redoc"),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

# SPA catch-all — must be LAST so /admin/, /api/, /static/, /media/ resolve first.
# This serves the React build's index.html for any non-API path so client-side
# routing works on direct URL hits in production.
urlpatterns += [
    re_path(r"^.*$", SPAFallbackView.as_view(), name="spa-fallback"),
]
