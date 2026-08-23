from __future__ import annotations

from django.db import transaction
from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.cases.models import Case

from .models import EconomicModel, EconomicParameter
from .permissions import EconPermission
from .serializers import (
    EconDeterministicResultSerializer,
    EconomicModelSerializer,
    EconomicParameterSerializer,
)
from .service import IncompleteModelError, run_deterministic


def _get_case(case_id: str) -> Case:
    return get_object_or_404(Case, case_id=case_id)


def _get_model(case: Case) -> EconomicModel | None:
    return EconomicModel.objects.filter(case=case).first()


class EconModelView(APIView):
    """GET / PUT the single EconomicModel (scalars) for a case (auto-upsert)."""

    permission_classes = (IsAuthenticated, EconPermission)

    def get(self, request: Request, case_id: str) -> Response:
        case = _get_case(case_id)
        self.check_object_permissions(request, case)
        model = _get_model(case)
        if model is None:
            return Response(None, status=status.HTTP_204_NO_CONTENT)
        return Response(EconomicModelSerializer(model).data)

    def put(self, request: Request, case_id: str) -> Response:
        case = _get_case(case_id)
        self.check_object_permissions(request, case)
        model = _get_model(case)
        serializer = EconomicModelSerializer(model, data=request.data, partial=False)
        serializer.is_valid(raise_exception=True)
        if model is None:
            serializer.save(case=case, created_by=request.user, last_edited_by=request.user)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        serializer.save(last_edited_by=request.user)
        return Response(serializer.data, status=status.HTTP_200_OK)


class EconParametersView(APIView):
    """GET list / PUT bulk-upsert the parameter set for a case.

    PUT accepts an array of parameter objects and upserts each by
    (key, alternative, year_index). Existing rows not in the payload are left
    untouched (values are edited in place, never silently dropped).
    """

    permission_classes = (IsAuthenticated, EconPermission)

    def get(self, request: Request, case_id: str) -> Response:
        case = _get_case(case_id)
        self.check_object_permissions(request, case)
        model = _get_model(case)
        if model is None:
            return Response([])
        params = model.parameters.all().select_related("created_by", "last_edited_by")
        return Response(EconomicParameterSerializer(params, many=True).data)

    @transaction.atomic
    def put(self, request: Request, case_id: str) -> Response:
        case = _get_case(case_id)
        self.check_object_permissions(request, case)

        model = _get_model(case)
        if model is None:
            return Response(
                {"detail": "Model ekonomi belum dibuat. Simpan parameter model terlebih dahulu."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        payload = request.data
        if not isinstance(payload, list):
            return Response(
                {"detail": "Payload harus berupa array parameter."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        serializer = EconomicParameterSerializer(data=payload, many=True)
        serializer.is_valid(raise_exception=True)

        for item in serializer.validated_data:
            EconomicParameter.objects.update_or_create(
                economic_model=model,
                key=item["key"],
                alternative=item["alternative"],
                year_index=item.get("year_index"),
                defaults={
                    "label": item.get("label", ""),
                    "value": item["value"],
                    "unit": item.get("unit", ""),
                    "param_type": item.get("param_type"),
                    "data_status": item.get("data_status"),
                    "source_reference": item.get("source_reference", ""),
                    "source_year": item.get("source_year"),
                    "notes": item.get("notes", ""),
                    "created_by": request.user,
                    "last_edited_by": request.user,
                },
            )

        params = model.parameters.all().select_related("created_by", "last_edited_by")
        return Response(EconomicParameterSerializer(params, many=True).data)


class EconComputeView(APIView):
    """POST compute → append-only EconDeterministicResult (or 400 with gaps)."""

    permission_classes = (IsAuthenticated, EconPermission)

    def post(self, request: Request, case_id: str) -> Response:
        case = _get_case(case_id)
        self.check_object_permissions(request, case)
        model = _get_model(case)
        if model is None:
            return Response(
                {"detail": "Model ekonomi belum dibuat untuk kasus ini."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        try:
            result = run_deterministic(model, computed_by=request.user)
        except IncompleteModelError as exc:
            return Response(
                {"detail": str(exc), "missing": exc.missing},
                status=status.HTTP_400_BAD_REQUEST,
            )
        return Response(
            EconDeterministicResultSerializer(result).data, status=status.HTTP_201_CREATED
        )


class EconResultListView(APIView):
    permission_classes = (IsAuthenticated, EconPermission)

    def get(self, request: Request, case_id: str) -> Response:
        case = _get_case(case_id)
        self.check_object_permissions(request, case)
        results = case.econ_deterministic_results.all().select_related("computed_by")
        return Response(EconDeterministicResultSerializer(results, many=True).data)


class EconResultLatestView(APIView):
    permission_classes = (IsAuthenticated, EconPermission)

    def get(self, request: Request, case_id: str) -> Response:
        case = _get_case(case_id)
        self.check_object_permissions(request, case)
        latest = case.econ_deterministic_results.order_by("-computed_at").first()
        if latest is None:
            return Response(None, status=status.HTTP_204_NO_CONTENT)
        return Response(EconDeterministicResultSerializer(latest).data)
