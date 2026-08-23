from django.urls import path

from .views import (
    EconComputeView,
    EconModelView,
    EconParametersView,
    EconResultLatestView,
    EconResultListView,
)

app_name = "econ"

urlpatterns = [
    path("cases/<str:case_id>/econ/model/", EconModelView.as_view(), name="model"),
    path("cases/<str:case_id>/econ/parameters/", EconParametersView.as_view(), name="parameters"),
    path("cases/<str:case_id>/econ/compute/", EconComputeView.as_view(), name="compute"),
    path("cases/<str:case_id>/econ/results/", EconResultListView.as_view(), name="results"),
    path("cases/<str:case_id>/econ/results/latest/", EconResultLatestView.as_view(), name="result_latest"),
]
