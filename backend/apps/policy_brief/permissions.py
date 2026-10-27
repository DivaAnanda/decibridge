"""Policy-brief permissions.

- Generate: Ketua KFT, HTA Analyst — case must be in `approved` or `locked`
  status (no point generating a brief before the decision has been signed off).
  The brief's section P ("UI tombol dan hak akses") assigns "Create New Version"
  to "Approver/Admin/HTA sesuai SOP"; Sekretaris KFT is deliberately not on that
  list. Round 5 item 5 took Admin IT off it: "Tidak boleh ... menerbitkan
  keputusan."
- List + download: the four content roles. A brief is case content, which Admin
  IT may not read.
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
    }
)

GENERATOR_ROLES = frozenset(
    {
        RoleSlug.KETUA_KFT,
        RoleSlug.HTA_ANALYST,
    }
)


class PolicyBriefPermission(BasePermission):
    """Content roles list and download; only Ketua KFT and HTA Analyst generate."""

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
