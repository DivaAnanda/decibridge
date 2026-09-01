"""Immutable decision snapshot captured when a case is locked (Phase V2).

Requested by the lecturer after acceptance testing HF_ARNI_ACEI_004:

    "Mohon diperbaiki agar pada saat keputusan di-lock, seluruh input dan output
     yang menjadi dasar keputusan (CEA, BIA, PSA bila digunakan, EtD, CBA,
     recommendation) tersimpan sebagai immutable snapshot untuk versi keputusan
     tersebut, sehingga hasil pada Analisis Ekonomi, BIA, Rekomendasi, Sign-Off,
     Brief, dan Versi selalu konsisten dan dapat direkonstruksi."

Before this, `CaseVersion` stored only soft FK *pointers* to the legacy CEA/BIA
results — nothing for the econ model, PSA, EtD or CBA. A case locked before the
econ migration therefore showed figures on Sign-Off but "no data" on the new
Analisis Ekonomi / BIA / PSA tabs. This module captures **values**, so every
consumer renders the same numbers for a locked version forever.

All imports are lazy: `apps.cases` is imported by every other app, so importing
them at module load would create a cycle.

The PSA scatter cloud is deliberately excluded (1000+ points); its summary and
CEAC curve are kept, which is what the UI and the brief actually render.
"""

from __future__ import annotations

from decimal import Decimal
from typing import Any

SNAPSHOT_VERSION = "1.0"


def _s(value: Any) -> Any:
    """JSON-safe: Decimals become strings so full precision survives."""
    if value is None:
        return None
    if isinstance(value, Decimal):
        return str(value)
    return value


def _econ_block(case) -> dict:
    from apps.econ.models import (
        EconBIAResult,
        EconDeterministicResult,
        EconomicModel,
        EconPSAResult,
    )

    block: dict[str, Any] = {"model": None, "parameters": [], "deterministic": None,
                             "bia": None, "psa": None}

    model = EconomicModel.objects.filter(case=case).first()
    if model is not None:
        block["model"] = {
            "horizon_years": model.horizon_years,
            "cost_discount_rate": _s(model.cost_discount_rate),
            "outcome_discount_rate": _s(model.outcome_discount_rate),
            "wtp_threshold": _s(model.wtp_threshold),
            "annual_budget_baseline": _s(model.annual_budget_baseline),
            "notes": model.notes,
        }
        block["parameters"] = [
            {
                "key": p.key,
                "label": p.display_label,
                "alternative": p.alternative,
                "year_index": p.year_index,
                "value": _s(p.value),
                "unit": p.unit,
                "param_type": p.param_type,
                "data_status": p.data_status,
                "source_reference": p.source_reference,
                "source_year": p.source_year,
                "distribution": p.distribution,
                "dist_param1": _s(p.dist_param1),
                "dist_param2": _s(p.dist_param2),
                "version": p.version,
            }
            for p in model.parameters.all().order_by("key", "alternative", "year_index")
        ]

    det = EconDeterministicResult.objects.filter(case=case).order_by("-computed_at").first()
    if det is not None:
        block["deterministic"] = {
            "id": det.pk,
            "total_cost_intervention": _s(det.total_cost_intervention),
            "total_cost_comparator": _s(det.total_cost_comparator),
            "total_qaly_intervention": _s(det.total_qaly_intervention),
            "total_qaly_comparator": _s(det.total_qaly_comparator),
            "incremental_cost": _s(det.incremental_cost),
            "incremental_qaly": _s(det.incremental_qaly),
            "icer": _s(det.icer),
            "nmb_intervention": _s(det.nmb_intervention),
            "nmb_comparator": _s(det.nmb_comparator),
            "inb": _s(det.inb),
            "wtp_threshold_used": _s(det.wtp_threshold_used),
            "decision_code": det.decision_code,
            "is_cost_effective": det.is_cost_effective,
            "is_dominant": det.is_dominant,
            "is_dominated": det.is_dominated,
            "per_year": det.per_year,
            "cost_breakdown": det.cost_breakdown,
            "clinical": det.clinical,
            "interpretation_text": det.interpretation_text,
            "algorithm_version": det.algorithm_version,
            "computed_at": det.computed_at.isoformat(),
        }

    bia = EconBIAResult.objects.filter(case=case).order_by("-computed_at").first()
    if bia is not None:
        block["bia"] = {
            "id": bia.pk,
            "cumulative_net_impact": _s(bia.cumulative_net_impact),
            "pct_of_total_baseline": _s(bia.pct_of_total_baseline),
            "annual_budget_baseline": _s(bia.annual_budget_baseline),
            "severity": bia.severity,
            "budget_score": bia.budget_score,
            "per_year": bia.per_year,
            "scenarios": bia.scenarios,
            "interpretation_text": bia.interpretation_text,
            "algorithm_version": bia.algorithm_version,
            "computed_at": bia.computed_at.isoformat(),
        }

    psa = EconPSAResult.objects.filter(case=case).order_by("-computed_at").first()
    if psa is not None:
        # Scatter cloud excluded on purpose — too large for a snapshot payload.
        block["psa"] = {
            "id": psa.pk,
            "n_simulations": psa.n_simulations,
            "random_seed": psa.random_seed,
            "wtp_base": _s(psa.wtp_base),
            "prob_cost_effective_base": _s(psa.prob_cost_effective_base),
            "mean_incremental_cost": _s(psa.mean_incremental_cost),
            "mean_incremental_qaly": _s(psa.mean_incremental_qaly),
            "ceac": psa.ceac,
            "base_case_incremental_cost": _s(psa.base_case_incremental_cost),
            "base_case_incremental_qaly": _s(psa.base_case_incremental_qaly),
            "interpretation_text": psa.interpretation_text,
            "algorithm_version": psa.algorithm_version,
            "computed_at": psa.computed_at.isoformat(),
        }

    return block


def _etd_block(case) -> dict:
    from apps.etd.aggregation import aggregate_domain, aggregate_overall
    from apps.etd.models import EtDAppraisal, EtDDomain

    domains = list(EtDDomain.objects.all().order_by("order"))
    by_domain: dict[int, list] = {d.pk: [] for d in domains}
    for a in EtDAppraisal.objects.filter(case=case).select_related("domain", "member"):
        by_domain[a.domain_id].append(a)

    per_domain = [aggregate_domain(d.slug, by_domain[d.pk]) for d in domains]
    overall = aggregate_overall(per_domain, total_domains=len(domains))

    return {
        "domains": [
            {
                "slug": d.slug,
                "name": d.display_name_id,
                "name_en": d.display_name_en,
                "order": d.order,
                "appraisal_count": agg.appraisal_count,
                "mean_judgement": _s(agg.mean_judgement),
                "median_judgement": _s(agg.median_judgement),
                "dominant_certainty": agg.dominant_certainty,
                "certainty_score": _s(agg.certainty_score),
                "combined_domain_score": _s(agg.combined_domain_score),
            }
            for d, agg in zip(domains, per_domain)
        ],
        "overall": {
            "domains_completed": overall.domains_completed,
            "domains_total": overall.domains_total,
            "evidence_strength_score": _s(overall.evidence_strength_score),
            "average_certainty": overall.average_certainty,
        },
        "appraisals": [
            {
                "domain": a.domain.slug,
                "member": a.member.full_name if a.member_id else None,
                "judgement": a.judgement,
                "certainty": a.certainty,
            }
            for a in EtDAppraisal.objects.filter(case=case).select_related("domain", "member")
        ],
    }


def _cba_block(case) -> list[dict]:
    return [
        {
            "order": c.order,
            "criterion_name": c.criterion_name,
            "field_reference": c.field_reference,
            "operator": c.operator,
            "expected_value": c.expected_value,
            "description": c.description,
            "is_satisfied": c.is_satisfied,
        }
        for c in case.cba_criteria.all().order_by("order")
    ]


def _recommendation_block(case) -> dict | None:
    rec = case.recommendations.order_by("-computed_at").first()
    if rec is None:
        return None
    return {
        "id": rec.pk,
        "evidence_strength_score": _s(rec.evidence_strength_score),
        "ce_score": _s(rec.ce_score),
        "budget_score": _s(rec.budget_score),
        "cba_score": _s(rec.cba_score),
        "composite_score": _s(rec.composite_score),
        "traffic_light": rec.traffic_light,
        "justification_text": rec.justification_text,
        "cba_criteria_count": rec.cba_criteria_count,
        "cba_satisfied_count": rec.cba_satisfied_count,
        "algorithm_version": rec.algorithm_version,
        "weight_aggregation_method": rec.weight_aggregation_method,
        "computed_at": rec.computed_at.isoformat(),
    }


def _approval_block(case) -> dict | None:
    approval = case.approvals.filter(decision="approved").order_by("-signed_at").first()
    if approval is None:
        return None
    return {
        "id": approval.pk,
        "decision": approval.decision,
        "signed_at": approval.signed_at.isoformat() if approval.signed_at else None,
        "approver": approval.approver.full_name if approval.approver_id else None,
        "approver_email": approval.approver.email if approval.approver_id else None,
    }


def _legacy_block(case) -> dict:
    """Legacy CEA-Quick / BIA rows, so pre-migration cases stay reconstructable."""
    cea = case.cea_results.order_by("-computed_at").first()
    bia = case.bia_results.order_by("-computed_at").first()
    return {
        "cea": (
            {
                "id": cea.pk,
                "icer_value": _s(cea.icer_value),
                "incremental_cost": _s(cea.incremental_cost),
                "incremental_effect": _s(cea.incremental_effect),
                "wtop_threshold_used": _s(cea.wtop_threshold_used),
                "dominance": cea.dominance,
                "ce_score": cea.ce_score,
                "interpretation_text": cea.interpretation_text,
                "computed_at": cea.computed_at.isoformat(),
            }
            if cea
            else None
        ),
        "bia": (
            {
                "id": bia.pk,
                "cumulative_impact": _s(bia.cumulative_impact),
                "pct_of_annual_budget": _s(bia.pct_of_annual_budget),
                "severity": bia.severity,
                "budget_score": bia.budget_score,
                "interpretation_text": bia.interpretation_text,
                "computed_at": bia.computed_at.isoformat(),
            }
            if bia
            else None
        ),
    }


def build_decision_snapshot(case) -> dict:
    """Capture every input and output underpinning the decision, by value."""
    return {
        "snapshot_version": SNAPSHOT_VERSION,
        "case": {
            "case_id": case.case_id,
            "case_title": case.case_title,
            "technology": case.technology,
            "comparator": case.comparator,
            "indication": case.indication,
            "population": case.population,
            "perspective": case.perspective,
            "status": case.status,
        },
        "econ": _econ_block(case),
        "etd": _etd_block(case),
        "cba": _cba_block(case),
        "recommendation": _recommendation_block(case),
        "approval": _approval_block(case),
        "legacy": _legacy_block(case),
    }
