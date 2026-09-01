"""Phase V2/V3 tests: immutable lock snapshot + completion gate.

Both behaviours were requested after the lecturer's acceptance test of
HF_ARNI_ACEI_004 (Sign-Off showed CEA/BIA figures while the econ tabs were
empty, and a case with EtD 4/9 could still be approved and locked).
"""

from __future__ import annotations

from decimal import Decimal

import pytest

from apps.cases.completeness import evaluate_readiness
from apps.cases.decision_snapshot import build_decision_snapshot
from apps.cases.models import CaseStatus, CaseVersion
from apps.cases.state_machine import transition
from apps.econ.models import EconomicModel, EconomicParameter
from apps.econ.service import run_bia, run_deterministic
from apps.econ.validation_fixtures import MODEL_SCALARS, VALIDATION_PARAMETERS
from apps.etd.models import EtDAppraisal, EtDDomain


@pytest.fixture
def econ_ready_case(pilot_case, hta_user):
    """Case with a complete econ model + deterministic + BIA results."""
    model = EconomicModel.objects.create(case=pilot_case, created_by=hta_user, **MODEL_SCALARS)
    for spec in VALIDATION_PARAMETERS:
        EconomicParameter.objects.create(
            economic_model=model,
            key=spec["key"],
            alternative=spec["alternative"],
            value=spec["value"],
            param_type=spec["param_type"],
            unit=spec.get("unit", ""),
            data_status=spec["data_status"],
            distribution=spec.get("distribution", "fixed"),
            dist_param1=spec.get("dist_param1"),
            dist_param2=spec.get("dist_param2"),
            created_by=hta_user,
        )
    run_deterministic(model, computed_by=hta_user)
    run_bia(model, computed_by=hta_user)
    return pilot_case


def _fill_all_etd(case, member):
    for domain in EtDDomain.objects.all():
        EtDAppraisal.objects.create(
            case=case, domain=domain, member=member, judgement=75, certainty="high"
        )


@pytest.mark.django_db
class TestDecisionSnapshot:
    def test_captures_every_module(self, econ_ready_case, hta_user, kft_member_user):
        _fill_all_etd(econ_ready_case, kft_member_user)
        snap = build_decision_snapshot(econ_ready_case)

        assert snap["case"]["case_id"] == econ_ready_case.case_id
        # Econ inputs AND outputs
        assert snap["econ"]["model"] is not None
        assert len(snap["econ"]["parameters"]) == len(VALIDATION_PARAMETERS)
        assert snap["econ"]["deterministic"] is not None
        assert snap["econ"]["bia"] is not None
        # EtD + CBA blocks exist even when empty
        assert snap["etd"]["overall"]["domains_total"] == 9
        assert "cba" in snap and "legacy" in snap

    def test_preserves_full_precision(self, econ_ready_case, hta_user):
        snap = build_decision_snapshot(econ_ready_case)
        det = snap["econ"]["deterministic"]
        assert Decimal(det["total_cost_intervention"]) == Decimal("18499451.85")
        assert abs(Decimal(det["icer"]) - Decimal("516105577.5669392")) <= Decimal("10")

    def test_written_on_lock(self, econ_ready_case, ketua_user, kft_member_user):
        _fill_all_etd(econ_ready_case, kft_member_user)
        econ_ready_case.status = CaseStatus.APPROVED
        econ_ready_case.save()

        transition(econ_ready_case, "lock", ketua_user)

        version = CaseVersion.objects.filter(case=econ_ready_case).order_by("-id").first()
        assert version is not None
        assert version.snapshot is not None
        assert version.snapshot["econ"]["deterministic"] is not None
        assert version.snapshot["etd"]["overall"]["domains_completed"] == 9


@pytest.mark.django_db
class TestCompletionGate:
    def test_incomplete_case_lists_gaps(self, pilot_case):
        readiness = evaluate_readiness(pilot_case)
        assert readiness["is_ready"] is False
        assert "Analisis ekonomi deterministik (CEA)" in readiness["missing"]

    def test_partial_etd_blocks_approval(self, econ_ready_case, ketua_user, kft_member_user):
        """The HF_ARNI_ACEI_004 scenario: 4/9 domains must NOT be approvable."""
        domains = list(EtDDomain.objects.all()[:4])
        for domain in domains:
            EtDAppraisal.objects.create(
                case=econ_ready_case, domain=domain, member=kft_member_user,
                judgement=75, certainty="high",
            )
        econ_ready_case.status = CaseStatus.IN_REVIEW
        econ_ready_case.save()

        from django.core.exceptions import ValidationError

        with pytest.raises(ValidationError) as exc:
            transition(econ_ready_case, "approve", ketua_user)
        assert "EtD" in str(exc.value)

    def test_full_dossier_allows_approval(self, econ_ready_case, ketua_user, kft_member_user):
        _fill_all_etd(econ_ready_case, kft_member_user)
        econ_ready_case.status = CaseStatus.IN_REVIEW
        econ_ready_case.save()

        transition(econ_ready_case, "approve", ketua_user)
        econ_ready_case.refresh_from_db()
        assert econ_ready_case.status == CaseStatus.APPROVED

    def test_readiness_checklist_is_explicit(self, econ_ready_case, kft_member_user):
        _fill_all_etd(econ_ready_case, kft_member_user)
        readiness = evaluate_readiness(econ_ready_case)
        keys = {r["key"] for r in readiness["requirements"]}
        assert {"economic_analysis", "budget_impact", "etd_domains", "recommendation"} <= keys
        etd = next(r for r in readiness["requirements"] if r["key"] == "etd_domains")
        assert etd["detail"] == "9/9 domain terisi"
        # CBA is advisory, never blocking
        cba = next(r for r in readiness["requirements"] if r["key"] == "cba_criteria")
        assert cba["mandatory"] is False

    def test_ungated_transitions_unaffected(self, pilot_case, hta_user):
        """submit() must still work on an incomplete draft."""
        transition(pilot_case, "submit", hta_user)
        pilot_case.refresh_from_db()
        assert pilot_case.status == CaseStatus.IN_REVIEW
