from django.urls import path

from .views import (
    EtDAppraisalDeleteView,
    EtDAppraisalListCreateView,
    EtDDomainListView,
    EtDSummaryView,
    ReferenceDetailView,
    ReferenceListCreateView,
)

app_name = "etd"

urlpatterns = [
    path("etd/domains/", EtDDomainListView.as_view(), name="domain_list"),
    path("cases/<str:case_id>/references/", ReferenceListCreateView.as_view(), name="reference_list"),
    path("cases/<str:case_id>/references/<int:pk>/", ReferenceDetailView.as_view(), name="reference_detail"),
    path("cases/<str:case_id>/etd/appraisals/", EtDAppraisalListCreateView.as_view(), name="appraisal_list"),
    path(
        "cases/<str:case_id>/etd/appraisals/<str:domain_slug>/",
        EtDAppraisalDeleteView.as_view(),
        name="appraisal_delete",
    ),
    path("cases/<str:case_id>/etd/summary/", EtDSummaryView.as_view(), name="summary"),
]
