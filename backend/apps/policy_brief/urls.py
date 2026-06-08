from django.urls import path

from .views import (
    PolicyBriefDetailView,
    PolicyBriefDownloadView,
    PolicyBriefListGenerateView,
)

urlpatterns = [
    path(
        "cases/<str:case_id>/policy-briefs/",
        PolicyBriefListGenerateView.as_view(),
        name="policy-brief-list-generate",
    ),
    path(
        "cases/<str:case_id>/policy-briefs/<int:brief_id>/",
        PolicyBriefDetailView.as_view(),
        name="policy-brief-detail",
    ),
    path(
        "cases/<str:case_id>/policy-briefs/<int:brief_id>/download/<str:fmt>/",
        PolicyBriefDownloadView.as_view(),
        name="policy-brief-download",
    ),
]
