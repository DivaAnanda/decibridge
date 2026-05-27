from __future__ import annotations

from typing import Iterable

from rest_framework.permissions import BasePermission
from rest_framework.request import Request
from rest_framework.views import APIView

from .models import RoleSlug


class HasRole(BasePermission):
    """Factory for role-based permission classes.

    Usage:
        class MyView(APIView):
            permission_classes = [IsAuthenticated, HasRole.any_of(RoleSlug.KETUA_KFT)]
    """

    required_roles: tuple[str, ...] = ()
    require_all: bool = False

    def has_permission(self, request: Request, view: APIView) -> bool:
        user = request.user
        if not user or not user.is_authenticated:
            return False
        if user.is_superuser:
            return True
        if not self.required_roles:
            return True
        user_roles = set(user.role_slugs)
        required = set(self.required_roles)
        return required.issubset(user_roles) if self.require_all else bool(required & user_roles)

    @classmethod
    def any_of(cls, *roles: str | RoleSlug) -> type[BasePermission]:
        return _build("HasAnyRole", roles, require_all=False)

    @classmethod
    def all_of(cls, *roles: str | RoleSlug) -> type[BasePermission]:
        return _build("HasAllRoles", roles, require_all=True)


def _build(
    class_name: str, roles: Iterable[str | RoleSlug], *, require_all: bool
) -> type[BasePermission]:
    slugs = tuple(r.value if isinstance(r, RoleSlug) else r for r in roles)
    return type(
        class_name,
        (HasRole,),
        {"required_roles": slugs, "require_all": require_all},
    )


# Convenience aliases for the 5 canonical roles.
IsAdminIT = HasRole.any_of(RoleSlug.ADMIN_IT)
IsHTAAnalyst = HasRole.any_of(RoleSlug.HTA_ANALYST)
IsFarmasiSekretaris = HasRole.any_of(RoleSlug.FARMASI_SEKRETARIS)
IsKFTMember = HasRole.any_of(RoleSlug.KFT_MEMBER)
IsKetuaKFT = HasRole.any_of(RoleSlug.KETUA_KFT)
