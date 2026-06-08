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
from django.utils import timezone

from apps.accounts.models import RoleSlug

from .models import CaseStatus, CaseVersion, CaseVersionStatus, CaseVersionTrigger

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

    # Sprint 10: snapshot the case as a CaseVersion row when locking.
    if action == "lock":
        _snapshot_locked_case(case, user)

    # Sprint 11: build the long-term archive when archiving.
    if action == "archive":
        # Lazy import — apps.archive depends on cases, would create a circular
        # import at module load.
        from apps.archive.service import archive_case

        archive_case(case, user)

    return case


# ---------------------------------------------------------------------------
# Versioning helpers (Sprint 10)
# ---------------------------------------------------------------------------


def _next_lock_version_number(case: Case) -> str:
    """Bump minor on every relock. v1.0 → v1.1 → v1.2 → ..."""
    prior = (
        CaseVersion.objects.filter(case=case, status=CaseVersionStatus.LOCKED)
        .order_by("-id")
        .first()
    )
    if prior is None:
        return "1.0"
    try:
        parts = prior.version_number.split(".")
        major = int(parts[0])
        minor = int(parts[1]) if len(parts) > 1 else 0
        return f"{major}.{minor + 1}"
    except (ValueError, IndexError):
        # Malformed prior version — defensive fallback. Bumps to v1.0 again
        # would clash with unique_together; bump to v99.X to avoid collision.
        return "99.0"


def _latest_pk(manager, order_field: str = "-pk") -> int | None:
    return manager.all().order_by(order_field).values_list("pk", flat=True).first()


def _snapshot_locked_case(case: Case, user: AbstractBaseUser) -> CaseVersion:
    """Create a CaseVersion row capturing the immutable artifact pointers at lock."""
    version_number = _next_lock_version_number(case)

    # Reverse-manager attribute names (defined in each app's FK related_name).
    # No app imports required; Django's ORM resolves them lazily.
    cea_id = _latest_pk(case.cea_results, "-computed_at")
    bia_id = _latest_pk(case.bia_results, "-computed_at")
    rec_id = _latest_pk(case.recommendations, "-computed_at")
    # Approval: only "approved" decisions are eligible to anchor the snapshot.
    approval_id = (
        case.approvals.filter(decision="approved")
        .order_by("-signed_at")
        .values_list("pk", flat=True)
        .first()
    )
    # Policy brief: latest completed.
    brief_id = (
        case.policy_briefs.filter(status="completed")
        .order_by("-version")
        .values_list("pk", flat=True)
        .first()
    )

    return CaseVersion.objects.create(
        case=case,
        version_number=version_number,
        status=CaseVersionStatus.LOCKED,
        trigger=CaseVersionTrigger.LOCKED,
        locked_at=timezone.now(),
        locked_by=user,
        lock_reason="",
        cea_result_id=cea_id,
        bia_result_id=bia_id,
        recommendation_id=rec_id,
        approval_id=approval_id,
        policy_brief_document_id=brief_id,
        created_by=user,
    )
