from django.urls import path

from .views import CEAComputeView, CEAInputView, CEAResultLatestView, CEAResultListView

app_name = "cea"

urlpatterns = [
    path("cases/<str:case_id>/cea/input/", CEAInputView.as_view(), name="input"),
    path("cases/<str:case_id>/cea/compute/", CEAComputeView.as_view(), name="compute"),
    path("cases/<str:case_id>/cea/results/", CEAResultListView.as_view(), name="results"),
    path("cases/<str:case_id>/cea/results/latest/", CEAResultLatestView.as_view(), name="result_latest"),
]
