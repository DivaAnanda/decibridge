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
from apps.cases.state_machine import transition as case_transition
from apps.recommendation.models import Recommendation

from .models import Approval, ApprovalDecision
from .permissions import ApprovalPermission
from .serializers import ApprovalReadSerializer, SignRequestSerializer


def _get_case(case_id: str) -> Case:
    return get_object_or_404(Case, case_id=case_id)


class ApprovalListView(APIView):
    """GET all approval events for a case (any viewer)."""

    permission_classes = (IsAuthenticated, ApprovalPermission)

    def get(self, request: Request, case_id: str) -> Response:
        case = _get_case(case_id)
        approvals = case.approvals.select_related("approver", "recommendation")
        return Response(ApprovalReadSerializer(approvals, many=True).data)


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
                if decision == ApprovalDecision.APPROVED.value:
                    case_transition(case, "approve", request.user)
                else:
                    case_transition(case, "send_back", request.user, reason=reason)

                approval = Approval.objects.create(
                    case=case,
                    recommendation=recommendation,
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
            ApprovalReadSerializer(approval).data, status=status.HTTP_201_CREATED
        )
