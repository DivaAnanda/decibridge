from __future__ import annotations

from django.contrib.auth import authenticate
from django.db import transaction
from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.audit.middleware import client_ip
from apps.audit.models import AuditLog
from apps.cases.models import Case, CaseStatus
from apps.cases.completeness import evaluate_readiness
from apps.cases.state_machine import transition as case_transition
from apps.recommendation.models import Recommendation

from .models import Approval, ApprovalDecision
from .permissions import ApprovalPermission
from .serializers import ApprovalReadSerializer, SignRequestSerializer


def _get_case(case_id: str) -> Case:
    return get_object_or_404(Case, case_id=case_id)


def _approval_refusal(case: Case, recommendation: Recommendation, data: dict) -> Response | None:
    """Why an approval may not be signed now, or None.

    Phase V3: the dossier must be complete. Round 5: the signature binds the
    latest recommendation and the current KFT decision, so a stale screen
    cannot sign something other than what the checks just passed.
    """
    latest = case.recommendations.order_by("-computed_at").first()
    if latest is None or recommendation.pk != latest.pk:
        return Response(
            {
                "detail": (
                    "Rekomendasi sudah dihitung ulang sejak halaman ini dimuat. Muat ulang tab "
                    "Sign-Off dan tinjau rekomendasi terbaru sebelum menandatangani."
                )
            },
            status=status.HTTP_409_CONFLICT,
        )
    readiness = evaluate_readiness(case)
    if not readiness["is_ready"]:
        return Response(
            {
                "detail": "Dossier belum lengkap: " + "; ".join(readiness["missing"]),
                "missing": readiness["missing"],
            },
            status=status.HTTP_422_UNPROCESSABLE_ENTITY,
        )
    expected = data.get("final_decision_id")
    current = case.final_decisions.first()
    if expected is not None and (current is None or current.pk != expected):
        return Response(
            {
                "detail": (
                    "Keputusan Final KFT berubah sejak halaman ini dimuat. Muat ulang tab "
                    "Sign-Off dan tinjau keputusan terbaru sebelum menandatangani."
                )
            },
            status=status.HTTP_409_CONFLICT,
        )
    return None


def _decision_context(case: Case) -> dict:
    from apps.cases.completeness import _revision_start

    latest = case.recommendations.order_by("-computed_at").first()
    return {
        "latest_recommendation_id": latest.pk if latest else None,
        "revision_start": _revision_start(case),
    }


class ApprovalListView(APIView):
    """GET all approval events for a case (any viewer)."""

    permission_classes = (IsAuthenticated, ApprovalPermission)

    def get(self, request: Request, case_id: str) -> Response:
        case = _get_case(case_id)
        approvals = case.approvals.select_related(
            "approver",
            "recommendation",
            "final_decision__decided_by",
            "final_decision__recommendation",
        )
        return Response(
            ApprovalReadSerializer(
                approvals, many=True, context={"request": request, **_decision_context(case)}
            ).data
        )


class ApprovalSignView(APIView):
    """POST: Ketua KFT signs off on a recommendation.

    Steps:
      1. Permission gate: Ketua KFT only.
      2. Case must be in_review (only state from which approval can fire).
      3. Confirmation checkbox must be true.
      4. Password must match request.user via check_password().
      5. Recommendation must belong to the same case and must exist.
      6. For approved: trigger case_transition('approve') (in_review → approved).
         For rejected / revision_requested: trigger case_transition('send_back')
         (in_review → draft) and require a reason.
      7. Append immutable Approval row + audit entry.
    """

    permission_classes = (IsAuthenticated, ApprovalPermission)

    def post(self, request: Request, case_id: str) -> Response:
        case = _get_case(case_id)
        if case.status != CaseStatus.IN_REVIEW:
            return Response(
                {"detail": f"Sign-off hanya bisa dilakukan saat status 'in_review' (saat ini: {case.status})."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        serializer = SignRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        recommendation = get_object_or_404(
            Recommendation, pk=data["recommendation_id"], case=case
        )

        # Password re-verification — check_password is constant-time per Django.
        verified = authenticate(
            request, username=request.user.email, password=data["password"]
        )
        if verified is None or verified.pk != request.user.pk:
            return Response(
                {"detail": "Sandi tidak cocok. Tanda tangan gagal."},
                status=status.HTTP_401_UNAUTHORIZED,
            )

        decision = data["decision"]
        reason = data.get("reason", "").strip()

        # State machine transition. Rejection/revision both send the case back to draft.
        try:
            with transaction.atomic():
                # Recording a final decision takes the same lock, so nothing can
                # change between the checks below and the signature that binds them.
                case = Case.objects.select_for_update().get(pk=case.pk)
                if decision == ApprovalDecision.APPROVED.value:
                    refusal = _approval_refusal(case, recommendation, data)
                    if refusal is not None:
                        return refusal
                    case_transition(case, "approve", request.user)
                else:
                    case_transition(case, "send_back", request.user, reason=reason)

                approval = Approval.objects.create(
                    case=case,
                    recommendation=recommendation,
                    final_decision=case.final_decisions.first(),
                    approver=request.user,
                    decision=decision,
                    confirmation_acknowledged=data["confirmation_acknowledged"],
                    password_verified_at=timezone.now(),
                    reason=reason,
                    ip_address=client_ip(request),
                    user_agent=request.META.get("HTTP_USER_AGENT", "")[:512],
                )
        except Exception as exc:  # state machine error or model error
            return Response({"detail": str(exc)}, status=status.HTTP_400_BAD_REQUEST)

        AuditLog.record(
            action=AuditLog.Action.APPROVE,
            actor=request.user,
            target=case,
            diff={
                "approval": {
                    "old": None,
                    "new": {
                        "decision": decision,
                        "recommendation_id": recommendation.pk,
                        "traffic_light": recommendation.traffic_light,
                        "final_decision_id": approval.final_decision_id,
                    },
                }
            },
            metadata={
                "approval_id": approval.pk,
                "reason": reason,
            },
            ip=client_ip(request),
            user_agent=request.META.get("HTTP_USER_AGENT", "")[:512],
        )

        return Response(
            ApprovalReadSerializer(
                approval, context={"request": request, **_decision_context(case)}
            ).data,
            status=status.HTTP_201_CREATED,
        )
