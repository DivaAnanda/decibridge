"""Policy-brief permissions.

- Generate: HTA Analyst, Sekretaris KFT, Ketua KFT — case must be in
  `approved` or `locked` status (no point generating a brief before the
  decision has been signed off).
- List + download: all 5 roles.
"""

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

GENERATOR_ROLES = frozenset(
    {
        RoleSlug.HTA_ANALYST,
        RoleSlug.FARMASI_SEKRETARIS,
        RoleSlug.KETUA_KFT,
    }
)


class PolicyBriefPermission(BasePermission):
    """All viewers can list+download; only HTA/Sekretaris/Ketua generate."""

    message = "Anda tidak memiliki izin untuk operasi ini pada dokumen kebijakan."

    def has_permission(self, request: Request, view: APIView) -> bool:
        if not (request.user and request.user.is_authenticated):
            return False
        user_roles = set(getattr(request.user, "role_slugs", []))
        if request.user.is_superuser:
            return True
        # GET → any viewer role is fine.
        if request.method in {"GET", "HEAD", "OPTIONS"}:
            return bool(user_roles & VIEWER_ROLES)
        # Anything else (POST = generate) → generator roles only.
        return bool(user_roles & GENERATOR_ROLES)
