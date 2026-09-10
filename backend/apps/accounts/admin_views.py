"""Admin IT user administration (Round 3, L4).

Acceptance testing found no way for Admin IT to do the job the brief assigns it:

    "Saya tidak menemukan menu untuk: melihat daftar pengguna; mengaktifkan/
     menonaktifkan akun; mengubah atau menetapkan role; memaksa reset kata sandi;
     melihat riwayat login; memantau kegagalan login."

Login events were already captured by `accounts.signals` into the append-only
AuditLog, so the history endpoints read existing data rather than adding a new
store.

Every mutation is audited, and an administrator cannot disable or demote their
own account -- locking the last administrator out is unrecoverable without
database access.
"""

from __future__ import annotations

from django.contrib.auth import get_user_model
from django.db.models import Q
from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.audit.middleware import client_ip
from apps.audit.models import AuditLog
from apps.versioning.serializers import AuditLogEntrySerializer

from .admin_serializers import AdminUserSerializer, AdminUserUpdateSerializer
from .models import Role
from .permissions import IsAdminIT

User = get_user_model()

LOGIN_ACTIONS = (
    AuditLog.Action.LOGIN_SUCCESS,
    AuditLog.Action.LOGIN_FAILED,
    AuditLog.Action.LOGOUT,
)
HISTORY_PAGE_SIZE = 100


def _audit(request: Request, *, action, target, diff=None, metadata=None) -> None:
    AuditLog.record(
        action=action,
        actor=request.user,
        target=target,
        diff=diff,
        metadata=metadata,
        ip=client_ip(request),
        user_agent=request.META.get("HTTP_USER_AGENT", "")[:512],
    )


class UserAdminListView(APIView):
    """GET /api/v1/admin/users/ - every account, newest first."""

    permission_classes = (IsAuthenticated, IsAdminIT)

    def get(self, request: Request) -> Response:
        users = User.objects.all().prefetch_related("groups__role").order_by("-date_joined")

        search = request.query_params.get("search", "").strip()
        if search:
            users = users.filter(
                Q(email__icontains=search) | Q(full_name__icontains=search)
            )

        active = request.query_params.get("is_active")
        if active in {"true", "false"}:
            users = users.filter(is_active=active == "true")

        return Response(
            AdminUserSerializer(users, many=True, context={"request": request}).data
        )


class UserAdminDetailView(APIView):
    """GET / PATCH /api/v1/admin/users/{id}/ - account status and roles."""

    permission_classes = (IsAuthenticated, IsAdminIT)

    def get(self, request: Request, user_id: int) -> Response:
        user = get_object_or_404(User, pk=user_id)
        return Response(AdminUserSerializer(user, context={"request": request}).data)

    def patch(self, request: Request, user_id: int) -> Response:
        target = get_object_or_404(User, pk=user_id)
        serializer = AdminUserUpdateSerializer(
            data=request.data, context={"target": target, "actor": request.user}
        )
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        before = {"is_active": target.is_active, "roles": sorted(target.role_slugs)}

        if "is_active" in data:
            target.is_active = data["is_active"]
            target.save(update_fields=["is_active"])

        if "roles" in data:
            groups = [r.group for r in Role.objects.filter(slug__in=data["roles"])]
            target.groups.set(groups)

        target.refresh_from_db()
        after = {"is_active": target.is_active, "roles": sorted(target.role_slugs)}

        if before != after:
            _audit(
                request,
                action=AuditLog.Action.UPDATE,
                target=target,
                diff={"before": before, "after": after},
                metadata={"module": "user_administration", "target_email": target.email},
            )

        return Response(AdminUserSerializer(target, context={"request": request}).data)


class UserForcePasswordResetView(APIView):
    """POST /api/v1/admin/users/{id}/force-password-reset/

    Flags the account so the next sign-in must set a new password. The
    administrator never chooses, sees, or transmits the password itself.
    """

    permission_classes = (IsAuthenticated, IsAdminIT)

    def post(self, request: Request, user_id: int) -> Response:
        target = get_object_or_404(User, pk=user_id)

        if target.must_change_password:
            return Response(
                {"detail": "Akun ini sudah ditandai wajib ganti kata sandi."},
                status=status.HTTP_409_CONFLICT,
            )

        target.must_change_password = True
        target.save(update_fields=["must_change_password"])

        _audit(
            request,
            action=AuditLog.Action.UPDATE,
            target=target,
            diff={"before": {"must_change_password": False},
                  "after": {"must_change_password": True}},
            metadata={"module": "user_administration", "target_email": target.email,
                      "reason": "forced_password_reset"},
        )

        return Response(AdminUserSerializer(target, context={"request": request}).data)


class LoginHistoryView(APIView):
    """GET /api/v1/admin/login-history/ - sign-in activity from the audit log.

    `?only_failed=true` narrows to failed attempts for monitoring; `?user_id=`
    scopes to one account.
    """

    permission_classes = (IsAuthenticated, IsAdminIT)

    def get(self, request: Request) -> Response:
        entries = AuditLog.objects.filter(action__in=LOGIN_ACTIONS).select_related("actor")

        if request.query_params.get("only_failed") == "true":
            entries = entries.filter(action=AuditLog.Action.LOGIN_FAILED)

        user_id = request.query_params.get("user_id")
        if user_id:
            entries = entries.filter(actor_id=user_id)

        entries = entries.order_by("-created_at")[:HISTORY_PAGE_SIZE]
        return Response(
            AuditLogEntrySerializer(entries, many=True, context={"request": request}).data
        )
