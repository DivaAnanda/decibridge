"""Orchestrator: pull Django model state → BriefContext → DOCX/PDF files.

Synchronous for Sprint 9 (HTTP request waits for generation). Decoupled so
Sprint 12 can wrap `generate()` in a Celery task without touching engine.py.

Layout on disk:
    {MEDIA_ROOT}/policy_briefs/{case_id}/v{N}.docx
    {MEDIA_ROOT}/policy_briefs/{case_id}/v{N}.pdf
"""

from __future__ import annotations

import hashlib
import logging
import os
from datetime import datetime
from decimal import Decimal
from pathlib import Path

from django.conf import settings
from django.utils import timezone

from apps.approval.models import Approval
from apps.bia.models import BIAInput, BIAResult, ProjectionHorizon, Severity
from apps.cases.models import Case, CaseStatus
from apps.cea.models import CEAInput, CEAResult, Dominance
from apps.etd.aggregation import aggregate_domain, aggregate_overall
from apps.etd.models import Certainty, EtDAppraisal, EtDDomain, Judgement, ReferenceCitation
from apps.recommendation.models import Recommendation, TrafficLight

from . import engine
from .models import GenerationStatus, PolicyBriefDocument

logger = logging.getLogger(__name__)


# ----------------------------------------------------------------------------
# Label mappers — TextChoices → localized strings
# ----------------------------------------------------------------------------


def _choice_label(choices_cls, value: str) -> str:
    """Return the localized label for a TextChoices value, or the raw value."""
    for choice in choices_cls.choices:
        if choice[0] == value:
            return str(choice[1])
    return value


def _localized_status(value: str) -> str:
    return _choice_label(CaseStatus, value)


def _localized_dominance(value: str) -> str:
    return _choice_label(Dominance, value)


def _localized_severity(value: str) -> str:
    return _choice_label(Severity, value)


def _localized_traffic_light(value: str) -> str:
    return _choice_label(TrafficLight, value)


def _localized_certainty(value: str | None) -> str:
    if not value:
        return "—"
    return _choice_label(Certainty, value)


def _localized_judgement(value: Decimal | None) -> str:
    if value is None:
        return "—"
    # Judgement is stored as int 0/25/50/75/100; aggregation may produce
    # fractional means. Map to the closest discrete band for the human-friendly
    # label; the numeric score is shown separately.
    rounded = int(round(float(value) / 25.0) * 25)
    rounded = max(0, min(100, rounded))
    return _choice_label(Judgement, rounded)


_DECISION_LABEL_ID = {
    "approved": "Disetujui",
    "rejected": "Ditolak",
    "revision_requested": "Minta revisi",
}


# ----------------------------------------------------------------------------
# Block builders — Django models → engine dataclasses
# ----------------------------------------------------------------------------


def _build_case_info(case: Case) -> engine.CaseInfo:
    return engine.CaseInfo(
        case_id=case.case_id,
        title=case.case_title,
        intervention=case.technology,
        comparator=case.comparator,
        indication=case.indication,
        population=case.population,
        setting=case.setting,
        perspective=case.get_perspective_display(),
        created_by_name=case.created_by.full_name or case.created_by.email,
        status=_localized_status(case.status),
    )


DECISION_LABEL_ID = {
    "dominant": "Dominan (lebih murah & lebih efektif)",
    "dominated": "Dominated (lebih mahal & kurang efektif)",
    "cost_effective": "Cost-effective pada WTP terpilih",
    "not_cost_effective": "Tidak cost-effective pada WTP terpilih",
}

BIA_SEVERITY_LABEL_ID = {
    "cost_saving": "Penghematan bersih",
    "manageable": "Dapat dikelola",
    "significant": "Signifikan",
    "prohibitive": "Prohibitif",
    "not_assessed": "Belum dinilai",
}


def _build_cea(case: Case) -> engine.CEABlock | None:
    """Cost-utility block.

    Reads the econ deterministic result (the current engine); falls back to the
    legacy CEA-Quick row so briefs for cases locked before the econ migration
    still render. Keeping both here is what makes the Brief agree with the
    Analisis Ekonomi tab for every case, old or new.
    """
    from apps.econ.models import EconDeterministicResult
    from apps.econ.scoring import ce_score_from_result

    det = EconDeterministicResult.objects.filter(case=case).order_by("-computed_at").first()
    if det is not None:
        return engine.CEABlock(
            icer=det.icer,
            dominance_label=DECISION_LABEL_ID.get(det.decision_code, det.decision_code),
            cost_drug=det.total_cost_intervention,
            cost_comparator=det.total_cost_comparator,
            efficacy_drug=det.total_qaly_intervention,
            efficacy_comparator=det.total_qaly_comparator,
            wtop_threshold=det.wtp_threshold_used,
            ce_score=ce_score_from_result(det),
            # The econ engine quantifies uncertainty via PSA, not a +/-20% band.
            sensitivity_low_icer=None,
            sensitivity_high_icer=None,
        )

    cea_result = CEAResult.objects.filter(case=case).order_by("-computed_at").first()
    if cea_result is None:
        return None

    cea_input = CEAInput.objects.filter(case=case).first()
    if cea_input is None:
        snap = cea_result.input_snapshot or {}
        cost_drug = Decimal(str(snap.get("drug_cost_per_unit", "0")))
        cost_comparator = Decimal(str(snap.get("comparator_cost_per_unit", "0")))
        eff_drug = Decimal(str(snap.get("drug_efficacy_value", "0")))
        eff_comparator = Decimal(str(snap.get("comparator_efficacy_value", "0")))
    else:
        cost_drug = cea_input.drug_cost_per_unit
        cost_comparator = cea_input.comparator_cost_per_unit
        eff_drug = cea_input.drug_efficacy_value
        eff_comparator = cea_input.comparator_efficacy_value

    return engine.CEABlock(
        icer=cea_result.icer_value,
        dominance_label=_localized_dominance(cea_result.dominance),
        cost_drug=cost_drug,
        cost_comparator=cost_comparator,
        efficacy_drug=eff_drug,
        efficacy_comparator=eff_comparator,
        wtop_threshold=cea_result.wtop_threshold_used,
        ce_score=Decimal(cea_result.ce_score),
        sensitivity_low_icer=cea_result.sensitivity_low_icer,
        sensitivity_high_icer=cea_result.sensitivity_high_icer,
    )


def _build_bia(case: Case) -> engine.BIABlock | None:
    """Budget-impact block: econ cost-offset BIA, legacy fallback."""
    from apps.econ.models import EconBIAResult

    econ_bia = EconBIAResult.objects.filter(case=case).order_by("-computed_at").first()
    if econ_bia is not None:
        rows: list[engine.BIAYearRow] = []
        for row in econ_bia.per_year or []:
            rows.append(
                engine.BIAYearRow(
                    year=int(row.get("year", 0)),
                    patients=int(Decimal(str(row.get("patients_intervention", "0")))),
                    cost_impact=Decimal(str(row.get("net_budget_impact", "0"))),
                    pct_of_budget=Decimal(str(row.get("pct_of_annual_baseline", "0"))).quantize(
                        Decimal("0.01")
                    ),
                )
            )
        return engine.BIABlock(
            rows=rows,
            cumulative_impact=econ_bia.cumulative_net_impact,
            cumulative_pct_of_budget=econ_bia.pct_of_total_baseline,
            severity_label=BIA_SEVERITY_LABEL_ID.get(econ_bia.severity, econ_bia.severity),
        )

    bia_result = BIAResult.objects.filter(case=case).order_by("-computed_at").first()
    if bia_result is None:
        return None

    bia_input = BIAInput.objects.filter(case=case).first()
    horizon = (
        ProjectionHorizon(bia_input.projection_horizon).value
        if bia_input
        else ProjectionHorizon.THREE_YEAR.value
    )
    eligible = bia_input.eligible_population if bia_input else 0

    rows = [
        engine.BIAYearRow(
            year=1,
            patients=eligible,
            cost_impact=bia_result.year1_net_impact,
            pct_of_budget=_pct_of_budget(bia_result.year1_net_impact, bia_input),
        )
    ]
    if horizon == 3:
        if bia_result.year2_net_impact_interpolated is not None:
            rows.append(
                engine.BIAYearRow(
                    year=2,
                    patients=eligible,
                    cost_impact=bia_result.year2_net_impact_interpolated,
                    pct_of_budget=_pct_of_budget(
                        bia_result.year2_net_impact_interpolated, bia_input
                    ),
                )
            )
        if bia_result.year3_net_impact is not None:
            rows.append(
                engine.BIAYearRow(
                    year=3,
                    patients=eligible,
                    cost_impact=bia_result.year3_net_impact,
                    pct_of_budget=_pct_of_budget(bia_result.year3_net_impact, bia_input),
                )
            )

    return engine.BIABlock(
        rows=rows,
        cumulative_impact=bia_result.cumulative_impact,
        cumulative_pct_of_budget=bia_result.pct_of_annual_budget * Decimal("100"),
        severity_label=_localized_severity(bia_result.severity),
    )


def _pct_of_budget(amount: Decimal, bia_input: BIAInput | None) -> Decimal:
    if bia_input is None or bia_input.budget_baseline == 0:
        return Decimal("0.00")
    return (amount / bia_input.budget_baseline * Decimal("100")).quantize(Decimal("0.01"))


def _build_etd(case: Case) -> engine.EtDBlock | None:
    domains = list(EtDDomain.objects.order_by("order"))
    if not domains:
        return None

    all_appraisals = list(
        EtDAppraisal.objects.filter(case=case).select_related("domain", "member")
    )
    if not all_appraisals:
        return engine.EtDBlock(
            rows=[
                engine.EtDDomainRow(
                    code=d.slug,
                    label=d.display_name_id,
                    mean_judgement=None,
                    judgement_label="—",
                    dominant_certainty="—",
                    member_count=0,
                )
                for d in domains
            ],
            aggregated_evidence_score=Decimal("0.00"),
            domains_filled=0,
            domains_total=len(domains),
        )

    rows: list[engine.EtDDomainRow] = []
    domain_aggregates = []
    for d in domains:
        domain_apps = [a for a in all_appraisals if a.domain_id == d.pk]
        agg = aggregate_domain(d.slug, domain_apps)
        domain_aggregates.append(agg)
        rows.append(
            engine.EtDDomainRow(
                code=d.slug,
                label=d.display_name_id,
                mean_judgement=agg.mean_judgement,
                judgement_label=_localized_judgement(agg.mean_judgement),
                dominant_certainty=_localized_certainty(agg.dominant_certainty),
                member_count=agg.appraisal_count,
            )
        )

    overall = aggregate_overall(domain_aggregates, total_domains=len(domains))
    return engine.EtDBlock(
        rows=rows,
        aggregated_evidence_score=overall.evidence_strength_score or Decimal("0.00"),
        domains_filled=overall.domains_completed,
        domains_total=overall.domains_total,
    )


def _build_cba(case: Case, recommendation: Recommendation | None) -> engine.CBABlock | None:
    criteria = list(case.cba_criteria.all().order_by("order"))
    if not criteria:
        return None

    rows = [
        engine.CBACriterionRow(
            label=c.criterion_name,
            operator=c.get_operator_display(),
            value=c.expected_value or "—",
            satisfied=c.is_satisfied,
            notes=c.description or "",
        )
        for c in criteria
    ]

    satisfied = sum(1 for c in criteria if c.is_satisfied)
    cba_score = (
        recommendation.cba_score
        if recommendation
        else Decimal("100.00") if satisfied == len(criteria) else
        (Decimal(satisfied) / Decimal(len(criteria)) * Decimal("100")).quantize(Decimal("0.01"))
    )
    return engine.CBABlock(
        rows=rows,
        cba_score=cba_score,
        satisfied_count=satisfied,
        total_count=len(criteria),
    )


def _build_recommendation(rec: Recommendation | None) -> engine.RecommendationBlock | None:
    if rec is None:
        return None
    return engine.RecommendationBlock(
        traffic_light=rec.traffic_light,
        traffic_light_label=_localized_traffic_light(rec.traffic_light),
        composite_score=rec.composite_score,
        evidence_score=rec.evidence_strength_score or Decimal("0.00"),
        ce_score=rec.ce_score or Decimal("0.00"),
        budget_score=rec.budget_score or Decimal("0.00"),
        cba_score=rec.cba_score,
        justification_text=rec.justification_text,
        computed_at=rec.computed_at,
        algorithm_version=rec.algorithm_version,
    )


def _build_references(case: Case) -> list[engine.ReferenceRow]:
    refs = list(
        ReferenceCitation.objects.filter(case=case).order_by("publication_year", "authors")
    )
    rows: list[engine.ReferenceRow] = []
    for idx, r in enumerate(refs, start=1):
        rows.append(
            engine.ReferenceRow(
                number=idx,
                citation=r.citation_text,
                authors=r.authors,
                year=r.publication_year,
                journal=r.journal_name,
                doi_or_url=r.doi_pmid or r.url,
            )
        )
    return rows


def _build_approvals(case: Case) -> list[engine.ApprovalRow]:
    approvals = list(
        Approval.objects.filter(case=case)
        .select_related("approver")
        .order_by("-signed_at")
    )
    rows: list[engine.ApprovalRow] = []
    for a in approvals:
        rows.append(
            engine.ApprovalRow(
                decision=a.decision,
                decision_label=_DECISION_LABEL_ID.get(a.decision, a.decision),
                approver_name=a.approver.full_name or a.approver.email,
                approver_email=a.approver.email,
                signed_at=a.signed_at,
                reason=a.reason or "",
                ip_address=a.ip_address or "",
            )
        )
    return rows


def build_context(case: Case, version: int) -> engine.BriefContext:
    """Assemble a BriefContext for `case` at the current snapshot of all data."""
    recommendation = (
        Recommendation.objects.filter(case=case).order_by("-computed_at").first()
    )
    return engine.BriefContext(
        case=_build_case_info(case),
        cea=_build_cea(case),
        bia=_build_bia(case),
        etd=_build_etd(case),
        cba=_build_cba(case, recommendation),
        recommendation=_build_recommendation(recommendation),
        references=_build_references(case),
        approvals=_build_approvals(case),
        generated_at=timezone.localtime(),
        version=version,
    )


# ----------------------------------------------------------------------------
# File IO + hashing + format conversion
# ----------------------------------------------------------------------------


def _output_dir(case: Case) -> Path:
    base = Path(settings.MEDIA_ROOT) / "policy_briefs" / case.case_id
    base.mkdir(parents=True, exist_ok=True)
    return base


def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _next_version_for(case: Case) -> int:
    last = (
        PolicyBriefDocument.objects.filter(case=case)
        .order_by("-version")
        .values_list("version", flat=True)
        .first()
    )
    return (last or 0) + 1


def _convert_docx_to_pdf(docx_path: Path, pdf_path: Path) -> None:
    """Convert DOCX → PDF, picking the converter based on platform.

    Windows (local dev):  MS Word via docx2pdf + COM. Pixel-perfect output.
    Linux  (Railway/etc): LibreOffice headless via `soffice --convert-to pdf`.

    Both paths must yield a file at `pdf_path` or raise.
    """
    import sys

    if sys.platform == "win32":
        _convert_docx_to_pdf_windows(docx_path, pdf_path)
    else:
        _convert_docx_to_pdf_linux(docx_path, pdf_path)

    if not pdf_path.exists():
        raise RuntimeError(
            f"PDF conversion completed without writing {pdf_path}. "
            "Check converter logs for details."
        )


def _convert_docx_to_pdf_windows(docx_path: Path, pdf_path: Path) -> None:
    """MS Word via docx2pdf + Windows COM.

    Django's runserver dispatches each request on a fresh thread, so we must
    call pythoncom.CoInitialize() per request — otherwise the second-and-onward
    generations fail with `CoInitialize has not been called` (CO_E_NOTINITIALIZED).
    """
    import pythoncom
    from docx2pdf import convert

    pythoncom.CoInitialize()
    try:
        convert(str(docx_path), str(pdf_path))
    finally:
        pythoncom.CoUninitialize()


def _convert_docx_to_pdf_linux(docx_path: Path, pdf_path: Path) -> None:
    """LibreOffice headless. `soffice` must be on PATH (apt install libreoffice).

    Note: soffice writes the output as `<basename>.pdf` into --outdir, so we
    rename it to the exact pdf_path the caller expects.
    """
    import shutil
    import subprocess

    if shutil.which("soffice") is None:
        raise RuntimeError(
            "soffice (LibreOffice) not found on PATH. "
            "Install with `apt install libreoffice` or equivalent."
        )

    result = subprocess.run(
        [
            "soffice",
            "--headless",
            "--convert-to",
            "pdf",
            "--outdir",
            str(pdf_path.parent),
            str(docx_path),
        ],
        capture_output=True,
        timeout=120,
        check=False,
    )
    if result.returncode != 0:
        raise RuntimeError(
            f"soffice convert failed (exit {result.returncode}): "
            f"{result.stderr.decode(errors='replace')[:500]}"
        )

    # soffice names the output after the input basename. Rename if necessary.
    produced = pdf_path.parent / (docx_path.stem + ".pdf")
    if produced != pdf_path and produced.exists():
        produced.replace(pdf_path)


def generate_brief(
    case: Case, generated_by, source_recommendation: Recommendation | None = None
) -> PolicyBriefDocument:
    """Build, persist, and convert. Synchronous. Returns the saved document row.

    Raises if any step fails; the row is then saved with status=FAILED.
    """
    version = _next_version_for(case)

    # Reserve the row first so even a failure has a paper trail.
    doc = PolicyBriefDocument.objects.create(
        case=case,
        version=version,
        status=GenerationStatus.GENERATING,
        generated_by=generated_by,
        source_recommendation_id=source_recommendation.pk if source_recommendation else None,
    )

    try:
        ctx = build_context(case, version=version)
        docx_bytes = engine.build_docx_bytes(ctx)

        out_dir = _output_dir(case)
        docx_path = out_dir / f"v{version}.docx"
        pdf_path = out_dir / f"v{version}.pdf"

        docx_path.write_bytes(docx_bytes)
        docx_sha = _sha256(docx_bytes)

        _convert_docx_to_pdf(docx_path, pdf_path)
        pdf_bytes = pdf_path.read_bytes()
        pdf_sha = _sha256(pdf_bytes)

        doc.docx_path = str(docx_path.relative_to(settings.MEDIA_ROOT)).replace(os.sep, "/")
        doc.pdf_path = str(pdf_path.relative_to(settings.MEDIA_ROOT)).replace(os.sep, "/")
        doc.docx_sha256 = docx_sha
        doc.pdf_sha256 = pdf_sha
        doc.docx_size_bytes = len(docx_bytes)
        doc.pdf_size_bytes = len(pdf_bytes)
        doc.status = GenerationStatus.COMPLETED
        doc.completed_at = timezone.now()
        doc.save(
            update_fields=[
                "docx_path",
                "pdf_path",
                "docx_sha256",
                "pdf_sha256",
                "docx_size_bytes",
                "pdf_size_bytes",
                "status",
                "completed_at",
            ]
        )
        return doc

    except Exception as exc:
        logger.exception("Policy brief generation failed for %s v%d", case.case_id, version)
        doc.error_message = str(exc)[:2000]
        doc.status = GenerationStatus.FAILED
        doc.completed_at = timezone.now()
        doc.save(update_fields=["error_message", "status", "completed_at"])
        raise


def absolute_path(relative_media_path: str) -> Path:
    """Return the absolute filesystem path for a doc.docx_path / doc.pdf_path value."""
    return Path(settings.MEDIA_ROOT) / relative_media_path
