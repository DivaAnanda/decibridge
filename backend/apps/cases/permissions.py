from __future__ import annotations

from rest_framework.permissions import SAFE_METHODS, BasePermission
from rest_framework.request import Request
from rest_framework.views import APIView

from apps.accounts.models import RoleSlug


CREATOR_ROLES = {RoleSlug.HTA_ANALYST, RoleSlug.FARMASI_SEKRETARIS}
EDITOR_ROLES = CREATOR_ROLES
# Roles that may read a case's clinical and economic content; every analysis app
# imports this set. Admin IT is left out on purpose (round 5 item 5, and the
# Panduan's least-privilege rule): it sees case metadata only.
VIEWER_ROLES = {
    RoleSlug.HTA_ANALYST,
    RoleSlug.FARMASI_SEKRETARIS,
    RoleSlug.KFT_MEMBER,
    RoleSlug.KETUA_KFT,
}
METADATA_ROLES = VIEWER_ROLES | {RoleSlug.ADMIN_IT}
METADATA_ACTIONS = {"list", "retrieve"}


def sees_metadata_only(user) -> bool:
    if user is None or not user.is_authenticated or user.is_superuser:
        return False
    roles = set(user.role_slugs)
    return bool(roles & METADATA_ROLES) and not roles & VIEWER_ROLES


class CanReadCaseContent(BasePermission):
    """Read-only views over a case's analysis: content roles only."""

    def has_permission(self, request: Request, view: APIView) -> bool:
        user = request.user
        if not user or not user.is_authenticated:
            return False
        if user.is_superuser:
            return True
        return request.method in SAFE_METHODS and bool(set(user.role_slugs) & VIEWER_ROLES)


class CasePermission(BasePermission):
    """Permission gate for case endpoints.

    Read (list/retrieve): any role. Admin IT alone gets list and retrieve only,
        through the metadata serializers.
    Create: HTA Analyst or Sekretaris KFT.
    Update / PATCH metadata: HTA Analyst or Sekretaris KFT, and only while
        the case is editable (draft / in_review).
    Add decision question: same as update.
    Transition: any viewer role passes here — the state machine itself
        enforces per-transition role rules (so Ketua KFT can approve, etc.).
    Delete: forbidden.
    """

    EDIT_ACTIONS = {"update", "partial_update", "add_question"}

    def has_permission(self, request: Request, view: APIView) -> bool:
        user = request.user
        if not user or not user.is_authenticated:
            return False
        if user.is_superuser:
            return True

        user_roles = set(user.role_slugs)
        if not user_roles & METADATA_ROLES:
            return False
        if not user_roles & VIEWER_ROLES:
            action = getattr(view, "action", None)
            return request.method in SAFE_METHODS and action in METADATA_ACTIONS

        if request.method in SAFE_METHODS:
            return True
        if request.method == "DELETE":
            return False

        action = getattr(view, "action", None)
        if action == "create":
            return bool(user_roles & CREATOR_ROLES)
        if action == "transition":
            # State machine does the per-transition role check.
            return True
        if action in self.EDIT_ACTIONS:
            return bool(user_roles & EDITOR_ROLES)
        # Unknown action — deny by default.
        return False

    def has_object_permission(self, request: Request, view: APIView, obj) -> bool:
        user = request.user
        if user.is_superuser:
            return True

        user_roles = set(user.role_slugs)
        if request.method in SAFE_METHODS:
            return bool(user_roles & METADATA_ROLES)

        action = getattr(view, "action", None)
        if action == "transition":
            # State machine validates source-status + role per transition.
            return bool(user_roles & VIEWER_ROLES)
        if obj.is_locked:
            return False
        return bool(user_roles & EDITOR_ROLES)
