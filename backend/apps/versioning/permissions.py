"""Versioning permissions: read-only, for the roles that may read case content."""

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
    }
)


class VersioningPermission(BasePermission):
    """Versions carry the locked figures, so Admin IT is not a reader (round 5 item 5)."""

    message = "Anda tidak memiliki akses ke riwayat versi kasus ini."

    def has_permission(self, request: Request, view: APIView) -> bool:
        if not (request.user and request.user.is_authenticated):
            return False
        if request.user.is_superuser:
            return True
        user_roles = set(getattr(request.user, "role_slugs", []))
        return bool(user_roles & VIEWER_ROLES)
