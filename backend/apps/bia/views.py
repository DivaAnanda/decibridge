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

from .engine import ALGORITHM_VERSION, BIAComputationInput, compute_bia
from .models import BIAInput, BIAResult
from .permissions import BIAPermission
from .serializers import BIAInputSerializer, BIAResultSerializer


def _get_case(case_id: str) -> Case:
    return get_object_or_404(Case, case_id=case_id)


class BIAInputView(APIView):
    permission_classes = (IsAuthenticated, BIAPermission)

    def get(self, request: Request, case_id: str) -> Response:
        case = _get_case(case_id)
        self.check_object_permissions(request, case)
        try:
            return Response(BIAInputSerializer(case.bia_input).data)
        except BIAInput.DoesNotExist:
            return Response(None, status=status.HTTP_204_NO_CONTENT)

    def put(self, request: Request, case_id: str) -> Response:
        case = _get_case(case_id)
        self.check_object_permissions(request, case)
        try:
            instance = case.bia_input
        except BIAInput.DoesNotExist:
            instance = None

        serializer = BIAInputSerializer(instance, data=request.data, partial=False)
        serializer.is_valid(raise_exception=True)
        if instance is None:
            serializer.save(case=case, created_by=request.user, last_edited_by=request.user)
            response_status = status.HTTP_201_CREATED
        else:
            serializer.save(last_edited_by=request.user)
            response_status = status.HTTP_200_OK
        return Response(serializer.data, status=response_status)


class BIAComputeView(APIView):
    permission_classes = (IsAuthenticated, BIAPermission)

    def post(self, request: Request, case_id: str) -> Response:
        case = _get_case(case_id)
        self.check_object_permissions(request, case)
        try:
            inp: BIAInput = case.bia_input
        except BIAInput.DoesNotExist:
            return Response(
                {"detail": "Input BIA belum diisi untuk kasus ini."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        compute_input = BIAComputationInput(
            eligible_population=inp.eligible_population,
            patient_uptake_year1=Decimal(inp.patient_uptake_year1),
            patient_uptake_year3=Decimal(inp.patient_uptake_year3),
            market_share_year1=Decimal(inp.market_share_year1),
            market_share_year3=Decimal(inp.market_share_year3),
            unit_cost_drug=Decimal(inp.unit_cost_drug),
            unit_cost_comparator=Decimal(inp.unit_cost_comparator),
            budget_baseline=Decimal(inp.budget_baseline),
            projection_horizon=inp.projection_horizon,
        )
        outcome = compute_bia(compute_input)

        result = BIAResult.objects.create(
            case=case,
            input_snapshot=compute_input.snapshot() | {"notes": inp.notes},
            year1_drug_cost=outcome.year1_drug_cost,
            year1_comparator_cost_displaced=outcome.year1_comparator_cost_displaced,
            year1_net_impact=outcome.year1_net_impact,
            year2_net_impact_interpolated=outcome.year2_net_impact_interpolated,
            year3_drug_cost=outcome.year3_drug_cost,
            year3_comparator_cost_displaced=outcome.year3_comparator_cost_displaced,
            year3_net_impact=outcome.year3_net_impact,
            cumulative_impact=outcome.cumulative_impact,
            pct_of_annual_budget=outcome.pct_of_annual_budget,
            severity=outcome.severity,
            direction=outcome.direction,
            budget_score=outcome.budget_score,
            interpretation_text=outcome.interpretation_text,
            algorithm_version=ALGORITHM_VERSION,
            computed_by=request.user,
        )

        AuditLog.record(
            action=AuditLog.Action.UPDATE,
            actor=request.user,
            target=case,
            diff={
                "bia_result": {
                    "old": None,
                    "new": {
                        "cumulative_impact": str(outcome.cumulative_impact),
                        "severity": outcome.severity,
                        "direction": outcome.direction,
                        "budget_score": outcome.budget_score,
                    },
                }
            },
            metadata={"bia_result_id": result.pk, "algorithm_version": ALGORITHM_VERSION},
            ip=client_ip(request),
            user_agent=request.META.get("HTTP_USER_AGENT", "")[:512],
        )

        return Response(BIAResultSerializer(result).data, status=status.HTTP_201_CREATED)


class BIAResultListView(APIView):
    permission_classes = (IsAuthenticated, BIAPermission)

    def get(self, request: Request, case_id: str) -> Response:
        case = _get_case(case_id)
        self.check_object_permissions(request, case)
        results = case.bia_results.all().select_related("computed_by")
        return Response(BIAResultSerializer(results, many=True).data)


class BIAResultLatestView(APIView):
    permission_classes = (IsAuthenticated, BIAPermission)

    def get(self, request: Request, case_id: str) -> Response:
        case = _get_case(case_id)
        self.check_object_permissions(request, case)
        latest = case.bia_results.order_by("-computed_at").first()
        if latest is None:
            return Response(None, status=status.HTTP_204_NO_CONTENT)
        return Response(BIAResultSerializer(latest).data)
