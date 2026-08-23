from __future__ import annotations

from rest_framework.permissions import SAFE_METHODS, BasePermission

from apps.cases.permissions import EDITOR_ROLES, VIEWER_ROLES


class EconPermission(BasePermission):
    """View: any viewer role. Edit / compute: HTA Analyst or Sekretaris KFT.

    Editing is blocked once the case is locked (mirrors CEAPermission).
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
        return bool(roles & EDITOR_ROLES)

    def has_object_permission(self, request, view, obj) -> bool:
        user = request.user
        if user.is_superuser:
            return True
        roles = set(user.role_slugs)
        if request.method in SAFE_METHODS:
            return bool(roles & VIEWER_ROLES)
        case = getattr(obj, "case", obj)
        if getattr(case, "is_locked", False):
            return False
        return bool(roles & EDITOR_ROLES)
