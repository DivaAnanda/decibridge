"""Versioning permissions — read-only for all authenticated viewers."""

from __future__ import annotations

from rest_framework.permissions import BasePermission
from rest_framework.request import Request
from rest_framework.views import APIView

from apps.accounts.models import RoleSlug

VIEWER_ROLES = frozenset(
    {
        RoleSlug.HTA_ANALYST,
        RoleSlug.FARMASI_SEKRETARIS,
        RoleSlug.KETUA_KFT,
        RoleSlug.KFT_MEMBER,
        RoleSlug.ADMIN_IT,
    }
)


class VersioningPermission(BasePermission):
    """Every authenticated role may read versions, timelines, and diffs."""

    message = "Anda tidak memiliki akses ke riwayat versi kasus ini."

    def has_permission(self, request: Request, view: APIView) -> bool:
        if not (request.user and request.user.is_authenticated):
            return False
        if request.user.is_superuser:
            return True
        user_roles = set(getattr(request.user, "role_slugs", []))
        return bool(user_roles & VIEWER_ROLES)
