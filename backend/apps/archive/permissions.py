"""Archive permissions: read-only.

The archive ACTION is gated separately in the state machine (Ketua KFT only).
The ArchiveRecord (date, retention, SHA-256 seal, artifact counts) is readable by
all five roles, so Admin IT can check backup and integrity. The manifest itself is
a full export of the case, so Admin IT may not download it (round 5 item 5).
"""

from __future__ import annotations

from rest_framework.permissions import BasePermission
from rest_framework.request import Request
from rest_framework.views import APIView

from apps.accounts.models import RoleSlug
from apps.cases.permissions import VIEWER_ROLES as CONTENT_ROLES

VIEWER_ROLES = frozenset(
    {
        RoleSlug.HTA_ANALYST,
        RoleSlug.FARMASI_SEKRETARIS,
        RoleSlug.KETUA_KFT,
        RoleSlug.KFT_MEMBER,
        RoleSlug.ADMIN_IT,
    }
)


class ArchivePermission(BasePermission):
    message = "Anda tidak memiliki akses ke arsip kasus ini."
    allowed_roles = VIEWER_ROLES

    def has_permission(self, request: Request, view: APIView) -> bool:
        if not (request.user and request.user.is_authenticated):
            return False
        if request.user.is_superuser:
            return True
        user_roles = set(getattr(request.user, "role_slugs", []))
        return bool(user_roles & self.allowed_roles)


class ArchiveManifestPermission(ArchivePermission):
    message = "Manifest arsip berisi isi kasus dan tidak tersedia untuk peran Anda."
    allowed_roles = frozenset(CONTENT_ROLES)
