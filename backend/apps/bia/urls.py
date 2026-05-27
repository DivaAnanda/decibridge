from django.urls import path

from .views import BIAComputeView, BIAInputView, BIAResultLatestView, BIAResultListView

app_name = "bia"

urlpatterns = [
    path("cases/<str:case_id>/bia/input/", BIAInputView.as_view(), name="input"),
    path("cases/<str:case_id>/bia/compute/", BIAComputeView.as_view(), name="compute"),
    path("cases/<str:case_id>/bia/results/", BIAResultListView.as_view(), name="results"),
    path("cases/<str:case_id>/bia/results/latest/", BIAResultLatestView.as_view(), name="result_latest"),
]
