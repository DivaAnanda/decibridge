from django.urls import path

from .views import ArchiveDetailView, ArchiveManifestDownloadView

urlpatterns = [
    path(
        "cases/<str:case_id>/archive/",
        ArchiveDetailView.as_view(),
        name="archive-detail",
    ),
    path(
        "cases/<str:case_id>/archive/manifest/",
        ArchiveManifestDownloadView.as_view(),
        name="archive-manifest",
    ),
]
