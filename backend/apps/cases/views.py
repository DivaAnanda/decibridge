from __future__ import annotations

from django.core.exceptions import PermissionDenied, ValidationError
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters, status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response

from apps.audit.middleware import client_ip
from apps.audit.models import AuditLog

from .models import Case, DecisionQuestion
from .permissions import CasePermission
from .serializers import (
    CaseCreateSerializer,
    CaseDetailSerializer,
    CaseListSerializer,
    DecisionQuestionSerializer,
    TransitionSerializer,
)
from .state_machine import transition as run_transition


class CaseViewSet(viewsets.ModelViewSet):
    """CRUD + state transitions for cases.

    Endpoints:
        GET    /api/v1/cases/                — list (filter by status)
        POST   /api/v1/cases/                — create (Sekretaris KFT / HTA Analyst)
        GET    /api/v1/cases/{case_id}/      — detail (lookup by slug)
        PATCH  /api/v1/cases/{case_id}/      — update editable fields
        POST   /api/v1/cases/{case_id}/transition/  — submit / approve / lock / etc.
        POST   /api/v1/cases/{case_id}/questions/   — append a decision question
    """

    queryset = Case.objects.select_related("created_by").prefetch_related(
        "decision_questions", "versions__created_by", "versions__locked_by"
    )
    permission_classes = (IsAuthenticated, CasePermission)
    lookup_field = "case_id"
    lookup_value_regex = r"[A-Z][A-Z0-9_]{2,63}"
    filter_backends = (DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter)
    filterset_fields = ("status", "perspective", "created_by")
    search_fields = ("case_id", "case_title", "technology", "comparator", "indication")
    ordering_fields = ("created_at", "updated_at", "case_id")
    ordering = ("-created_at",)

    def get_serializer_class(self):
        if self.action == "list":
            return CaseListSerializer
        if self.action == "create":
            return CaseCreateSerializer
        return CaseDetailSerializer

    def create(self, request: Request, *args, **kwargs) -> Response:
        write_serializer = self.get_serializer(data=request.data)
        write_serializer.is_valid(raise_exception=True)
        case = write_serializer.save()
        read_serializer = CaseDetailSerializer(case, context=self.get_serializer_context())
        return Response(read_serializer.data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=["post"], url_path="transition")
    def transition(self, request: Request, case_id: str | None = None) -> Response:
        case = self.get_object()
        serializer = TransitionSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        action_name = serializer.validated_data["action"]
        reason = serializer.validated_data.get("reason", "")

        previous_status = case.status
        try:
            run_transition(case, action_name, request.user, reason=reason)
        except KeyError as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_400_BAD_REQUEST)
        except ValidationError as exc:
            payload: dict = {"detail": exc.message}
            # Phase V3: an incomplete dossier returns the checklist gaps so the
            # Sign-Off UI can list exactly what is still required.
            missing = (getattr(exc, "params", None) or {}).get("missing")
            if missing:
                payload["missing"] = missing
                return Response(payload, status=status.HTTP_422_UNPROCESSABLE_ENTITY)
            return Response(payload, status=status.HTTP_400_BAD_REQUEST)
        except PermissionDenied as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_403_FORBIDDEN)

        AuditLog.record(
            action=AuditLog.Action.UPDATE,
            actor=request.user,
            target=case,
            diff={"status": {"old": previous_status, "new": case.status}},
            metadata={"transition": action_name, "reason": reason},
            ip=client_ip(request),
            user_agent=request.META.get("HTTP_USER_AGENT", "")[:512],
        )

        return Response(
            CaseDetailSerializer(case, context=self.get_serializer_context()).data
        )

    @action(detail=True, methods=["get"], url_path="readiness")
    def readiness(self, request: Request, case_id: str | None = None) -> Response:
        """Decision-readiness checklist shown on Sign-Off (Phase V3).

        Returns the same requirement list the approve/lock gate enforces, so the
        rule is explicit in the UI rather than only surfacing as a rejection.
        """
        from .completeness import evaluate_readiness

        return Response(evaluate_readiness(self.get_object()))

    @action(detail=True, methods=["post"], url_path="questions")
    def add_question(self, request: Request, case_id: str | None = None) -> Response:
        case = self.get_object()
        if not case.is_editable:
            return Response(
                {"detail": "Case is not editable in its current status."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        serializer = DecisionQuestionSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        next_order = (
            DecisionQuestion.objects.filter(case=case)
            .order_by("-order")
            .values_list("order", flat=True)
            .first()
            or 0
        ) + 1
        serializer.save(case=case, order=next_order)
        return Response(serializer.data, status=status.HTTP_201_CREATED)
