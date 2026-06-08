from django.urls import path

from .views import (
    VersionDiffView,
    VersionListView,
    VersionStateView,
    VersionTimelineView,
)

urlpatterns = [
    path(
        "cases/<str:case_id>/versions/",
        VersionListView.as_view(),
        name="version-list",
    ),
    path(
        "cases/<str:case_id>/versions/diff/",
        VersionDiffView.as_view(),
        name="version-diff",
    ),
    path(
        "cases/<str:case_id>/versions/<int:version_id>/timeline/",
        VersionTimelineView.as_view(),
        name="version-timeline",
    ),
    path(
        "cases/<str:case_id>/versions/<int:version_id>/state/",
        VersionStateView.as_view(),
        name="version-state",
    ),
]
