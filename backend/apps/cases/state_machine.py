"""Case status state machine.

Allowed transitions and the roles permitted to invoke each. Centralised here
so views, signals, and management commands all enforce the same rules.

Transitions:
    draft → in_review        (hta_analyst, farmasi_sekretaris)
    in_review → draft        (ketua_kft only — rejection invoked by the Sign-Off flow)
    in_review → approved     (ketua_kft only)
    approved → in_review     (revision requested: ketua_kft only — undo own approval before lock)
    approved → locked        (ketua_kft only — locks evidence for v1.x)
    locked → archived        (admin_it, ketua_kft)
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from django.core.exceptions import PermissionDenied, ValidationError

from apps.accounts.models import RoleSlug

from .models import CaseStatus

if TYPE_CHECKING:
    from django.contrib.auth.models import AbstractBaseUser

    from .models import Case


@dataclass(frozen=True)
class Transition:
    name: str
    source: frozenset[str]
    target: str
    allowed_roles: frozenset[str]
    requires_reason: bool = False


TRANSITIONS: dict[str, Transition] = {
    "submit": Transition(
        name="submit",
        source=frozenset({CaseStatus.DRAFT}),
        target=CaseStatus.IN_REVIEW,
        allowed_roles=frozenset({RoleSlug.HTA_ANALYST, RoleSlug.FARMASI_SEKRETARIS}),
    ),
    "send_back": Transition(
        name="send_back",
        source=frozenset({CaseStatus.IN_REVIEW}),
        target=CaseStatus.DRAFT,
        allowed_roles=frozenset({RoleSlug.KETUA_KFT}),
        requires_reason=True,
    ),
    "approve": Transition(
        name="approve",
        source=frozenset({CaseStatus.IN_REVIEW}),
        target=CaseStatus.APPROVED,
        allowed_roles=frozenset({RoleSlug.KETUA_KFT}),
    ),
    "request_revision": Transition(
        name="request_revision",
        source=frozenset({CaseStatus.APPROVED}),
        target=CaseStatus.IN_REVIEW,
        allowed_roles=frozenset({RoleSlug.KETUA_KFT}),
        requires_reason=True,
    ),
    "lock": Transition(
        name="lock",
        source=frozenset({CaseStatus.APPROVED}),
        target=CaseStatus.LOCKED,
        allowed_roles=frozenset({RoleSlug.KETUA_KFT}),
    ),
    "archive": Transition(
        name="archive",
        source=frozenset({CaseStatus.LOCKED}),
        target=CaseStatus.ARCHIVED,
        allowed_roles=frozenset({RoleSlug.ADMIN_IT, RoleSlug.KETUA_KFT}),
    ),
}


def allowed_transitions_for(case: Case, user: AbstractBaseUser) -> list[Transition]:
    """Which transitions can `user` invoke on `case` right now?"""
    if not user.is_authenticated:
        return []
    user_roles = set(getattr(user, "role_slugs", []))
    if user.is_superuser:
        user_roles = {r.value for r in RoleSlug}
    return [
        t
        for t in TRANSITIONS.values()
        if case.status in t.source and (user_roles & t.allowed_roles)
    ]


def transition(
    case: Case,
    action: str,
    user: AbstractBaseUser,
    *,
    reason: str = "",
) -> Case:
    """Apply `action` to `case`. Mutates and saves.

    Raises:
        KeyError: unknown action name.
        ValidationError: case is not in a state from which `action` can fire.
        PermissionDenied: user lacks the required role.
    """
    try:
        t = TRANSITIONS[action]
    except KeyError as exc:
        raise KeyError(f"Unknown transition '{action}'") from exc

    if case.status not in t.source:
        raise ValidationError(
            f"Transition '{action}' not allowed from status '{case.status}'.",
            code="invalid_transition",
        )

    user_roles = set(getattr(user, "role_slugs", []))
    if not user.is_superuser and not (user_roles & t.allowed_roles):
        raise PermissionDenied(
            f"Role(s) {sorted(user_roles) or 'none'} cannot perform '{action}'."
        )

    if t.requires_reason and not reason.strip():
        raise ValidationError(
            f"Transition '{action}' requires a non-empty reason.",
            code="reason_required",
        )

    case.status = t.target
    case.save(update_fields=["status", "updated_at"])
    return case
