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
def complete_dossier(case_in_review, hta_user, kft_member_user):
    """Satisfy `evaluate_readiness`: deterministic econ + BIA + all 9 EtD domains.

    Brief generation is gated on dossier completeness (Round 3 H1), so every
    generation fixture has to build a case that would genuinely pass sign-off.
    """
    from apps.econ.models import EconBIAResult, EconDeterministicResult
    from apps.etd.models import EtDAppraisal, EtDDomain

    EconDeterministicResult.objects.create(
        case=case_in_review,
        input_snapshot={"dummy": True},
        total_cost_intervention=Decimal("18499451.85"),
        total_cost_comparator=Decimal("5199411.1161"),
        total_qaly_intervention=Decimal("0.655"),
        total_qaly_comparator=Decimal("0.62923"),
        incremental_cost=Decimal("13300040.7339"),
        incremental_qaly=Decimal("0.5000"),
        icer=Decimal("10000000"),
        nmb_intervention=Decimal("1"),
        nmb_comparator=Decimal("0"),
        inb=Decimal("1"),
        wtp_threshold_used=Decimal("250000000"),
        decision_code="cost_effective",
        is_cost_effective=True,
        is_dominant=False,
        is_dominated=False,
        interpretation_text="seed",
        algorithm_version="2.0.0",
        computed_by=hta_user,
    )
    EconBIAResult.objects.create(
        case=case_in_review,
        input_snapshot={"dummy": True},
        cumulative_net_impact=Decimal("1500000000"),
        pct_of_total_baseline=Decimal("3.0000"),
        annual_budget_baseline=Decimal("50000000000"),
        severity="manageable",
        budget_score=80,
        per_year=[],
        interpretation_text="seed",
        algorithm_version="2.0.0",
        computed_by=hta_user,
    )
    for domain in EtDDomain.objects.all():
        EtDAppraisal.objects.create(
            case=case_in_review,
            domain=domain,
            member=kft_member_user,
            judgement=75,
            certainty="high",
        )
    return case_in_review


@pytest.fixture
def approved_case_with_rec(complete_dossier, case_in_review, hta_user, ketua_user):
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
