from django.urls import path

from .views import (
    EconBIAComputeView,
    EconBIAResultLatestView,
    EconBIAResultListView,
    EconComputeView,
    EconModelView,
    EconParametersView,
    EconPSAComputeView,
    EconPSAResultLatestView,
    EconResultLatestView,
    EconResultListView,
    EconValidateView,
    EconValidationTemplateView,
)

app_name = "econ"

urlpatterns = [
    path("cases/<str:case_id>/econ/model/", EconModelView.as_view(), name="model"),
    path("cases/<str:case_id>/econ/parameters/", EconParametersView.as_view(), name="parameters"),
    path("cases/<str:case_id>/econ/compute/", EconComputeView.as_view(), name="compute"),
    path("cases/<str:case_id>/econ/results/", EconResultListView.as_view(), name="results"),
    path("cases/<str:case_id>/econ/results/latest/", EconResultLatestView.as_view(), name="result_latest"),
    path("cases/<str:case_id>/econ/bia/compute/", EconBIAComputeView.as_view(), name="bia_compute"),
    path("cases/<str:case_id>/econ/bia/results/", EconBIAResultListView.as_view(), name="bia_results"),
    path("cases/<str:case_id>/econ/bia/results/latest/", EconBIAResultLatestView.as_view(), name="bia_result_latest"),
    path("cases/<str:case_id>/econ/psa/compute/", EconPSAComputeView.as_view(), name="psa_compute"),
    path("cases/<str:case_id>/econ/psa/results/latest/", EconPSAResultLatestView.as_view(), name="psa_result_latest"),
    path("cases/<str:case_id>/econ/validate/template/", EconValidationTemplateView.as_view(), name="validate_template"),
    path("cases/<str:case_id>/econ/validate/", EconValidateView.as_view(), name="validate"),
]
