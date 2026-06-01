from __future__ import annotations

from rest_framework.permissions import SAFE_METHODS, BasePermission

from apps.accounts.models import RoleSlug
from apps.cases.permissions import VIEWER_ROLES


class ApprovalPermission(BasePermission):
    """Read: any viewer role. Sign: Ketua KFT only.

    Locked cases reject all writes; the model itself is append-only so
    update/delete don't apply.
    """

    def has_permission(self, request, view) -> bool:
        user = request.user
        if not user or not user.is_authenticated:
            return False
        if user.is_superuser:
            return True
        roles = set(user.role_slugs)
        if not roles & VIEWER_ROLES:
            return False
        if request.method in SAFE_METHODS:
            return True
        return RoleSlug.KETUA_KFT in roles
