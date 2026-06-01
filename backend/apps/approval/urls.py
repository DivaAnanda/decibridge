from django.urls import path

from .views import ApprovalListView, ApprovalSignView

app_name = "approval"

urlpatterns = [
    path("cases/<str:case_id>/approvals/", ApprovalListView.as_view(), name="list"),
    path("cases/<str:case_id>/approvals/sign/", ApprovalSignView.as_view(), name="sign"),
]
