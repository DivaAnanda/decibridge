"""Policy-brief test fixtures.

The PDF converter (`docx2pdf.convert`) needs MS Word and is slow. We monkey-patch
it to simply write a fake PDF byte string so the API tests can run anywhere.
The DOCX side of the pipeline runs for real.
"""

from __future__ import annotations

from decimal import Decimal
from pathlib import Path

import pytest

from apps.policy_brief import service
from apps.recommendation.models import Recommendation


@pytest.fixture(autouse=True)
def fake_docx2pdf(monkeypatch):
    """Replace MS Word with a no-op that drops a small fake PDF on disk."""

    def _fake_convert(docx_path: Path, pdf_path: Path) -> None:
        Path(pdf_path).write_bytes(b"%PDF-1.4\n%fake-pdf-from-test\n%%EOF\n")

    monkeypatch.setattr(service, "_convert_docx_to_pdf", _fake_convert)


@pytest.fixture
def approved_case_with_rec(case_in_review, hta_user, ketua_user):
    """A case in `approved` status, with one Recommendation already computed."""
    from apps.cases.state_machine import transition as case_transition

    rec = Recommendation.objects.create(
        case=case_in_review,
        input_snapshot={"dummy": True},
        evidence_strength_score=Decimal("90"),
        ce_score=Decimal("100"),
        budget_score=Decimal("80"),
        cba_score=Decimal("100"),
        composite_score=Decimal("92.00"),
        traffic_light="green",
        justification_text="Strong evidence + cost-saving + clean CBA.",
        cba_criteria_count=0,
        cba_satisfied_count=0,
        algorithm_version="1.0.0",
        weight_aggregation_method="mean",
        computed_by=hta_user,
    )
    case_transition(case_in_review, "approve", ketua_user)
    case_in_review.refresh_from_db()
    return case_in_review, rec


@pytest.fixture
def case_in_review(pilot_case, hta_user):
    """Walk the pilot case to `in_review`. Mirrors the approval-app fixture."""
    from apps.cases.state_machine import transition as case_transition

    case_transition(pilot_case, "submit", hta_user)
    pilot_case.refresh_from_db()
    return pilot_case
