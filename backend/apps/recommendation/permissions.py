from __future__ import annotations

from rest_framework.permissions import SAFE_METHODS, BasePermission

from apps.accounts.models import RoleSlug
from apps.cases.permissions import VIEWER_ROLES

CBA_EDITOR_ROLES = {RoleSlug.FARMASI_SEKRETARIS, RoleSlug.KETUA_KFT, RoleSlug.HTA_ANALYST}
WEIGHT_VOTER_ROLES = {RoleSlug.KFT_MEMBER, RoleSlug.KETUA_KFT}
COMPUTE_ROLES = {RoleSlug.HTA_ANALYST, RoleSlug.FARMASI_SEKRETARIS, RoleSlug.KETUA_KFT}


class _BaseScoped(BasePermission):
    write_roles: frozenset[str] = frozenset()

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
        return bool(roles & self.write_roles)

    def has_object_permission(self, request, view, obj) -> bool:
        user = request.user
        if user.is_superuser:
            return True
        roles = set(user.role_slugs)
        if request.method in SAFE_METHODS:
            return bool(roles & VIEWER_ROLES)
        case = getattr(obj, "case", None)
        if case and getattr(case, "is_locked", False):
            return False
        return bool(roles & self.write_roles)


class CBAPermission(_BaseScoped):
    write_roles = frozenset(CBA_EDITOR_ROLES)


class WeightVotePermission(_BaseScoped):
    """KFT members + chair may vote; users can only edit their OWN row."""

    write_roles = frozenset(WEIGHT_VOTER_ROLES)

    def has_object_permission(self, request, view, obj) -> bool:
        if not super().has_object_permission(request, view, obj):
            return False
        if request.method in SAFE_METHODS:
            return True
        return obj.member_id == request.user.pk


class ComputePermission(BasePermission):
    """Any HTA/Sekretaris/Ketua can trigger a recommendation compute.
    All viewers can read past recommendations."""

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
        return bool(roles & COMPUTE_ROLES)
