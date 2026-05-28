from __future__ import annotations

from rest_framework.permissions import SAFE_METHODS, BasePermission

from apps.accounts.models import RoleSlug
from apps.cases.permissions import VIEWER_ROLES

REFERENCE_EDITOR_ROLES = {RoleSlug.HTA_ANALYST, RoleSlug.FARMASI_SEKRETARIS}
APPRAISAL_EDITOR_ROLES = {RoleSlug.KFT_MEMBER, RoleSlug.KETUA_KFT}


class ReferencePermission(BasePermission):
    """All viewers read; HTA Analyst + Sekretaris KFT manage references."""

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
        return bool(roles & REFERENCE_EDITOR_ROLES)


class EtDAppraisalPermission(BasePermission):
    """KFT Members and the Ketua KFT submit appraisals — and only their own.

    Read: any viewer role.
    Write/Update/Delete: must own the appraisal and hold KFT_MEMBER or
    KETUA_KFT (or be superuser).
    Locked cases are read-only.
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
        return bool(roles & APPRAISAL_EDITOR_ROLES)

    def has_object_permission(self, request, view, obj) -> bool:
        user = request.user
        if user.is_superuser:
            return True
        roles = set(user.role_slugs)
        if request.method in SAFE_METHODS:
            return bool(roles & VIEWER_ROLES)
        if getattr(obj.case, "is_locked", False):
            return False
        if not (roles & APPRAISAL_EDITOR_ROLES):
            return False
        return obj.member_id == user.pk
