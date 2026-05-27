from __future__ import annotations

from decimal import Decimal

from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.audit.middleware import client_ip
from apps.audit.models import AuditLog
from apps.cases.models import Case

from .engine import ALGORITHM_VERSION, CEAComputationInput, compute_cea
from .models import CEAInput, CEAResult
from .permissions import CEAPermission
from .serializers import CEAInputSerializer, CEAResultSerializer


def _get_case(case_id: str) -> Case:
    return get_object_or_404(Case, case_id=case_id)


class CEAInputView(APIView):
    """GET / PUT the single CEAInput row for a case (auto-upsert)."""

    permission_classes = (IsAuthenticated, CEAPermission)

    def get(self, request: Request, case_id: str) -> Response:
        case = _get_case(case_id)
        self.check_object_permissions(request, case)
        try:
            return Response(CEAInputSerializer(case.cea_input).data)
        except CEAInput.DoesNotExist:
            return Response(None, status=status.HTTP_204_NO_CONTENT)

    def put(self, request: Request, case_id: str) -> Response:
        case = _get_case(case_id)
        self.check_object_permissions(request, case)

        try:
            instance = case.cea_input
        except CEAInput.DoesNotExist:
            instance = None

        serializer = CEAInputSerializer(instance, data=request.data, partial=False)
        serializer.is_valid(raise_exception=True)
        if instance is None:
            serializer.save(case=case, created_by=request.user, last_edited_by=request.user)
            response_status = status.HTTP_201_CREATED
        else:
            serializer.save(last_edited_by=request.user)
            response_status = status.HTTP_200_OK
        return Response(serializer.data, status=response_status)


class CEAComputeView(APIView):
    """POST compute → creates an immutable CEAResult."""

    permission_classes = (IsAuthenticated, CEAPermission)

    def post(self, request: Request, case_id: str) -> Response:
        case = _get_case(case_id)
        self.check_object_permissions(request, case)
        try:
            inp: CEAInput = case.cea_input
        except CEAInput.DoesNotExist:
            return Response(
                {"detail": "CEA inputs belum diisi untuk kasus ini."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        compute_input = CEAComputationInput(
            drug_cost_per_unit=Decimal(inp.drug_cost_per_unit),
            comparator_cost_per_unit=Decimal(inp.comparator_cost_per_unit),
            drug_efficacy_value=Decimal(inp.drug_efficacy_value),
            comparator_efficacy_value=Decimal(inp.comparator_efficacy_value),
            wtop_threshold=Decimal(inp.wtop_threshold),
            efficacy_metric=inp.efficacy_metric,
            metric_label=inp.metric_label,
        )
        outcome = compute_cea(compute_input)

        result = CEAResult.objects.create(
            case=case,
            input_snapshot=compute_input.snapshot()
            | {
                "patient_population_size": inp.patient_population_size,
                "data_source": inp.data_source,
                "evidence_year": inp.evidence_year,
                "notes": inp.notes,
            },
            incremental_cost=outcome.incremental_cost,
            incremental_effect=outcome.incremental_effect,
            icer_value=outcome.icer_value,
            wtop_threshold_used=outcome.wtop_threshold_used,
            dominance=outcome.dominance,
            ce_score=outcome.ce_score,
            sensitivity_low_icer=outcome.sensitivity_low_icer,
            sensitivity_high_icer=outcome.sensitivity_high_icer,
            threshold_sensitivity_flag=outcome.threshold_sensitivity_flag,
            interpretation_text=outcome.interpretation_text,
            algorithm_version=ALGORITHM_VERSION,
            computed_by=request.user,
        )

        AuditLog.record(
            action=AuditLog.Action.UPDATE,
            actor=request.user,
            target=case,
            diff={
                "cea_result": {
                    "old": None,
                    "new": {
                        "icer_value": str(outcome.icer_value) if outcome.icer_value else None,
                        "dominance": outcome.dominance,
                        "ce_score": outcome.ce_score,
                    },
                }
            },
            metadata={"cea_result_id": result.pk, "algorithm_version": ALGORITHM_VERSION},
            ip=client_ip(request),
            user_agent=request.META.get("HTTP_USER_AGENT", "")[:512],
        )

        return Response(CEAResultSerializer(result).data, status=status.HTTP_201_CREATED)


class CEAResultListView(APIView):
    """List past CEA computations for a case (most recent first)."""

    permission_classes = (IsAuthenticated, CEAPermission)

    def get(self, request: Request, case_id: str) -> Response:
        case = _get_case(case_id)
        self.check_object_permissions(request, case)
        results = case.cea_results.all().select_related("computed_by")
        return Response(CEAResultSerializer(results, many=True).data)


class CEAResultLatestView(APIView):
    permission_classes = (IsAuthenticated, CEAPermission)

    def get(self, request: Request, case_id: str) -> Response:
        case = _get_case(case_id)
        self.check_object_permissions(request, case)
        latest = case.cea_results.order_by("-computed_at").first()
        if latest is None:
            return Response(None, status=status.HTTP_204_NO_CONTENT)
        return Response(CEAResultSerializer(latest).data)
