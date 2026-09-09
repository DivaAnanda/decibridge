"""Round 3: archiving runs a stricter integrity check than approve/lock.

Archiving turns a case into the hospital's formal decision record, so a case
locked before the completeness gate existed must not slip in unexamined.
"""

from __future__ import annotations

from decimal import Decimal

import pytest
from django.core.exceptions import ValidationError

from apps.cases.integrity import (
    FLAG_OK,
    FLAG_REQUIRES_REMEDIATION,
    evaluate_integrity,
)
from apps.cases.state_machine import transition

pytestmark = pytest.mark.django_db


def _force_locked(case) -> None:
    """Put a case in `locked` without walking the gated transitions."""
    from apps.cases.models import Case, CaseStatus

    Case.objects.filter(pk=case.pk).update(status=CaseStatus.LOCKED)
    case.refresh_from_db()


def test_case_missing_econ_and_etd_fails_integrity(pilot_case):
    _force_locked(pilot_case)

    report = evaluate_integrity(pilot_case)

    assert report["is_valid"] is False
    assert report["suggested_flag"] == FLAG_REQUIRES_REMEDIATION
    assert "Analisis ekonomi deterministik (CEA)" in report["failures"]


def test_locked_case_without_snapshot_fails_integrity(pilot_case):
    """The _004 shape: locked, but carrying no immutable snapshot."""
    _force_locked(pilot_case)

    report = evaluate_integrity(pilot_case)

    assert "Snapshot keputusan tersimpan dan tidak dapat diubah" in report["failures"]


def test_archive_transition_is_refused_when_integrity_fails(pilot_case, admin_it_user):
    _force_locked(pilot_case)

    with pytest.raises(ValidationError) as exc:
        transition(
            pilot_case, "archive", admin_it_user, reason="retensi", enforce_completeness=True
        )

    assert exc.value.code == "integrity_check_failed"
    assert exc.value.params["missing"]


def test_archive_still_works_without_the_opt_in_gate(pilot_case, admin_it_user):
    """Internal flows and migrations must not be blocked by the gate."""
    _force_locked(pilot_case)

    transition(pilot_case, "archive", admin_it_user, reason="retensi")

    pilot_case.refresh_from_db()
    assert pilot_case.status == "archived"


def test_role_check_still_precedes_the_integrity_gate(pilot_case, kft_member_user):
    """An unauthorised caller gets 403 semantics, not 'integrity failed'."""
    from django.core.exceptions import PermissionDenied

    _force_locked(pilot_case)

    with pytest.raises(PermissionDenied):
        transition(
            pilot_case, "archive", kft_member_user, reason="x", enforce_completeness=True
        )
