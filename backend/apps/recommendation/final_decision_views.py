"""Keputusan Final KFT: the human decision beside the system verdict (round 5 item 3).

  GET  /api/v1/cases/{case_id}/final-decisions/  history, newest first
  POST /api/v1/cases/{case_id}/final-decisions/  record a new decision (Anggota/Ketua KFT)
"""

from __future__ import annotations

from django.db import transaction
from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.audit.middleware import client_ip
from apps.audit.models import AuditLog
from apps.cases.models import Case

from .models import FinalDecision
from .permissions import FinalDecisionPermission
from .serializers import FinalDecisionCreateSerializer, FinalDecisionSerializer


def _context(case: Case) -> dict:
    from apps.cases.completeness import _revision_start

    latest = case.recommendations.order_by("-computed_at").first()
    return {
        "latest_recommendation_id": latest.pk if latest else None,
        "revision_start": _revision_start(case),
    }


class FinalDecisionListCreateView(APIView):
    permission_classes = (IsAuthenticated, FinalDecisionPermission)

    def get(self, request: Request, case_id: str) -> Response:
        case = get_object_or_404(Case, case_id=case_id)
        rows = case.final_decisions.select_related("decided_by", "recommendation")
        return Response(
            FinalDecisionSerializer(rows, many=True, context=_context(case)).data
        )

    def post(self, request: Request, case_id: str) -> Response:
        case = get_object_or_404(Case, case_id=case_id)
        serializer = FinalDecisionCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        with transaction.atomic():
            case = Case.objects.select_for_update().get(pk=case.pk)
            # Once signed, the signature is bound to the decision it saw; a new one
            # needs the case sent back first.
            if not case.is_editable:
                return Response(
                    {
                        "detail": (
                            "Keputusan final hanya dapat dicatat selama kasus berstatus Draft "
                            "atau Dalam Tinjauan."
                        )
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )

            recommendation = case.recommendations.order_by("-computed_at").first()
            if recommendation is None:
                return Response(
                    {
                        "detail": (
                            "Belum ada rekomendasi sistem. Hitung rekomendasi terlebih dahulu, "
                            "lalu catat keputusan final atas rekomendasi itu."
                        )
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )
            decision = FinalDecision.objects.create(
                case=case,
                recommendation=recommendation,
                decision=serializer.validated_data["decision"],
                reason=serializer.validated_data["reason"],
                decided_by=request.user,
            )
        AuditLog.record(
            action=AuditLog.Action.CREATE,
            actor=request.user,
            target=decision,
            diff={
                "final_decision": {
                    "old": None,
                    "new": {
                        "decision": decision.decision,
                        "reason": decision.reason,
                        "recommendation_id": recommendation.pk,
                    },
                }
            },
            metadata={"case_id": case.case_id},
            ip=client_ip(request),
            user_agent=request.META.get("HTTP_USER_AGENT", "")[:512],
        )
        return Response(
            FinalDecisionSerializer(decision, context=_context(case)).data,
            status=status.HTTP_201_CREATED,
        )
