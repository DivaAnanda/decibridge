"""Archive test fixtures."""

from __future__ import annotations

from decimal import Decimal

import pytest

from apps.cases.state_machine import transition as case_transition
from apps.recommendation.models import Recommendation


@pytest.fixture
def locked_case(pilot_case, hta_user, ketua_user):
    """Case driven through: draft → submit → recommendation → approve → lock.

    Not yet archived. Used as the starting point for archive tests.
    """
    case_transition(pilot_case, "submit", hta_user)
    Recommendation.objects.create(
        case=pilot_case,
        input_snapshot={"dummy": True},
        evidence_strength_score=Decimal("90"),
        ce_score=Decimal("100"),
        budget_score=Decimal("80"),
        cba_score=Decimal("100"),
        composite_score=Decimal("92.00"),
        traffic_light="green",
        justification_text="Test.",
        cba_criteria_count=0,
        cba_satisfied_count=0,
        algorithm_version="1.0.0",
        weight_aggregation_method="mean",
        computed_by=hta_user,
    )
    case_transition(pilot_case, "approve", ketua_user)
    case_transition(pilot_case, "lock", ketua_user)
    pilot_case.refresh_from_db()
    return pilot_case


@pytest.fixture
def archived_case(locked_case, ketua_user):
    """Case driven all the way through to archived. Triggers manifest generation."""
    case_transition(locked_case, "archive", ketua_user, reason="Digantikan versi baru")
    locked_case.refresh_from_db()
    return locked_case


@pytest.fixture
def archived_case_with_brief(locked_case, hta_user, monkeypatch, tmp_path, settings):
    """A locked case with a real generated policy brief on disk.

    Files land under tmp_path so a tampering test can modify them without
    touching the developer's media directory. The PDF converter is stubbed -
    it needs LibreOffice or Word - while the DOCX is written for real, which is
    what the hash check reads back.
    """
    from pathlib import Path

    from apps.policy_brief import service

    settings.MEDIA_ROOT = str(tmp_path)

    def _fake_convert(docx_path: Path, pdf_path: Path) -> None:
        Path(pdf_path).write_bytes(b"%PDF-1.4\n%fake-pdf-from-test\n%%EOF\n")

    monkeypatch.setattr(service, "_convert_docx_to_pdf", _fake_convert)

    latest_rec = locked_case.recommendations.order_by("-computed_at").first()
    brief = service.generate_brief(
        case=locked_case,
        generated_by=hta_user,
        source_recommendation=latest_rec,
    )
    return locked_case, brief
