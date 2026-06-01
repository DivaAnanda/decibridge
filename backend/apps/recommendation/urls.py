from django.urls import path

from .views import (
    CBACriterionDetailView,
    CBACriterionListCreateView,
    RecommendationComputeView,
    RecommendationLatestView,
    RecommendationListView,
    WeightsSummaryView,
    WeightVoteListUpsertView,
)

app_name = "recommendation"

urlpatterns = [
    path("cases/<str:case_id>/weights/", WeightVoteListUpsertView.as_view(), name="weights"),
    path("cases/<str:case_id>/weights/summary/", WeightsSummaryView.as_view(), name="weights_summary"),
    path("cases/<str:case_id>/cba/", CBACriterionListCreateView.as_view(), name="cba_list"),
    path("cases/<str:case_id>/cba/<int:pk>/", CBACriterionDetailView.as_view(), name="cba_detail"),
    path(
        "cases/<str:case_id>/recommendation/compute/",
        RecommendationComputeView.as_view(),
        name="compute",
    ),
    path("cases/<str:case_id>/recommendation/results/", RecommendationListView.as_view(), name="results"),
    path(
        "cases/<str:case_id>/recommendation/results/latest/",
        RecommendationLatestView.as_view(),
        name="result_latest",
    ),
]
