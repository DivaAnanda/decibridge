"""Round 3: the integrity audit flags legacy cases instead of deleting them."""

from __future__ import annotations

from io import StringIO

import pytest
from django.core.management import call_command

from apps.cases.models import Case, CaseStatus, IntegrityFlag

pytestmark = pytest.mark.django_db


def _force_status(case, status: str) -> None:
    Case.objects.filter(pk=case.pk).update(status=status)
    case.refresh_from_db()


def _run(**kwargs) -> str:
    out = StringIO()
    call_command("audit_case_integrity", stdout=out, **kwargs)
    return out.getvalue()


def test_draft_cases_are_not_audited(pilot_case):
    output = _run()

    assert "No locked or archived cases" in output
    pilot_case.refresh_from_db()
    assert pilot_case.integrity_flag == IntegrityFlag.OK


def test_incomplete_locked_case_is_flagged_with_its_reasons(pilot_case):
    """The HF_ARNI_ACEI_004 shape."""
    _force_status(pilot_case, CaseStatus.LOCKED)

    _run()

    pilot_case.refresh_from_db()
    assert pilot_case.integrity_flag == IntegrityFlag.REQUIRES_REMEDIATION
    assert "Analisis ekonomi deterministik (CEA)" in pilot_case.integrity_notes
    assert pilot_case.integrity_checked_at is not None


def test_flagged_case_is_kept_not_deleted(pilot_case):
    """The lecturer reuses HF_ARNI_ACEI_004 as a regression fixture."""
    _force_status(pilot_case, CaseStatus.LOCKED)

    _run()

    assert Case.objects.filter(pk=pilot_case.pk).exists()


def test_dry_run_reports_without_writing(pilot_case):
    _force_status(pilot_case, CaseStatus.LOCKED)

    output = _run(dry_run=True)

    pilot_case.refresh_from_db()
    assert "dry run" in output
    assert pilot_case.integrity_flag == IntegrityFlag.OK
    assert pilot_case.integrity_checked_at is None


def test_rerunning_clears_a_case_that_has_been_remediated(pilot_case):
    _force_status(pilot_case, CaseStatus.LOCKED)
    Case.objects.filter(pk=pilot_case.pk).update(
        integrity_flag=IntegrityFlag.REQUIRES_REMEDIATION, integrity_notes="stale"
    )

    # Still incomplete, so it stays flagged rather than silently clearing.
    _run()

    pilot_case.refresh_from_db()
    assert pilot_case.integrity_flag == IntegrityFlag.REQUIRES_REMEDIATION


def test_single_case_can_be_audited_by_id(pilot_case):
    _force_status(pilot_case, CaseStatus.LOCKED)

    output = _run(case_id=pilot_case.case_id)

    assert pilot_case.case_id in output
