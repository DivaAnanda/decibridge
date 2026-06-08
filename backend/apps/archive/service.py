"""Orchestrator: Django models → manifest dict → JSON file on disk → ArchiveRecord row.

Called synchronously by the state machine's `archive` transition. Like the
policy-brief service, this is wrapped Celery-ready in Sprint 12 if needed.
"""

from __future__ import annotations

import logging
import os
from datetime import timedelta
from pathlib import Path

from django.conf import settings
from django.utils import timezone

from apps.approval.models import Approval
from apps.audit.models import AuditLog
from apps.bia.models import BIAResult
from apps.cases.models import Case, CaseVersion
from apps.cea.models import CEAResult
from apps.etd.models import EtDAppraisal, ReferenceCitation
from apps.policy_brief.models import PolicyBriefDocument
from apps.recommendation.models import Recommendation

from . import engine
from .models import DEFAULT_RETENTION_YEARS, ArchiveRecord

logger = logging.getLogger(__name__)


def _case_meta(case: Case) -> dict:
    return {
        "case_id": case.case_id,
        "case_title": case.case_title,
        "intervention": case.technology,
        "comparator": case.comparator,
        "indication": case.indication,
        "population": case.population,
        "setting": case.setting,
        "perspective": case.perspective,
        "status": case.status,
        "created_at": case.created_at,
        "created_by_email": case.created_by.email,
        "updated_at": case.updated_at,
    }


def _cea_row(r: CEAResult) -> dict:
    return {
        "id": r.pk,
        "icer_value": r.icer_value,
        "incremental_cost": r.incremental_cost,
        "incremental_effect": r.incremental_effect,
        "wtop_threshold_used": r.wtop_threshold_used,
        "dominance": r.dominance,
        "ce_score": r.ce_score,
        "sensitivity_low_icer": r.sensitivity_low_icer,
        "sensitivity_high_icer": r.sensitivity_high_icer,
        "algorithm_version": r.algorithm_version,
        "computed_at": r.computed_at,
        "input_snapshot": r.input_snapshot,
    }


def _bia_row(r: BIAResult) -> dict:
    return {
        "id": r.pk,
        "year1_net_impact": r.year1_net_impact,
        "year2_net_impact_interpolated": r.year2_net_impact_interpolated,
        "year3_net_impact": r.year3_net_impact,
        "cumulative_impact": r.cumulative_impact,
        "pct_of_annual_budget": r.pct_of_annual_budget,
        "severity": r.severity,
        "direction": r.direction,
        "budget_score": r.budget_score,
        "algorithm_version": r.algorithm_version,
        "computed_at": r.computed_at,
        "input_snapshot": r.input_snapshot,
    }


def _etd_row(a: EtDAppraisal) -> dict:
    return {
        "id": a.pk,
        "domain_slug": a.domain.slug,
        "member_email": a.member.email,
        "judgement": a.judgement,
        "certainty": a.certainty,
        "narrative": a.narrative,
        "created_at": a.created_at,
        "updated_at": a.updated_at,
    }


def _reference_row(r: ReferenceCitation) -> dict:
    return {
        "id": r.pk,
        "reference_type": r.reference_type,
        "citation_text": r.citation_text,
        "authors": r.authors,
        "publication_year": r.publication_year,
        "title": r.title,
        "journal_name": r.journal_name,
        "doi_pmid": r.doi_pmid,
        "url": r.url,
        "evidence_summary": r.evidence_summary,
        "created_at": r.created_at,
    }


def _recommendation_row(r: Recommendation) -> dict:
    return {
        "id": r.pk,
        "evidence_strength_score": r.evidence_strength_score,
        "ce_score": r.ce_score,
        "budget_score": r.budget_score,
        "cba_score": r.cba_score,
        "composite_score": r.composite_score,
        "traffic_light": r.traffic_light,
        "justification_text": r.justification_text,
        "cba_criteria_count": r.cba_criteria_count,
        "cba_satisfied_count": r.cba_satisfied_count,
        "algorithm_version": r.algorithm_version,
        "weight_aggregation_method": r.weight_aggregation_method,
        "computed_at": r.computed_at,
    }


def _approval_row(a: Approval) -> dict:
    return {
        "id": a.pk,
        "decision": a.decision,
        "approver_email": a.approver.email,
        "confirmation_acknowledged": a.confirmation_acknowledged,
        "password_verified_at": a.password_verified_at,
        "signed_at": a.signed_at,
        "reason": a.reason,
        "ip_address": a.ip_address,
        "recommendation_id": a.recommendation_id,
    }


def _case_version_row(v: CaseVersion) -> dict:
    return {
        "id": v.pk,
        "version_number": v.version_number,
        "status": v.status,
        "trigger": v.trigger,
        "locked_at": v.locked_at,
        "locked_by_email": v.locked_by.email if v.locked_by else None,
        "lock_reason": v.lock_reason,
        "created_at": v.created_at,
        "cea_result_id": v.cea_result_id,
        "bia_result_id": v.bia_result_id,
        "recommendation_id": v.recommendation_id,
        "approval_id": v.approval_id,
        "policy_brief_document_id": v.policy_brief_document_id,
    }


def _policy_brief_row(b: PolicyBriefDocument) -> dict:
    return {
        "id": b.pk,
        "version": b.version,
        "status": b.status,
        "docx_path": b.docx_path,
        "pdf_path": b.pdf_path,
        "docx_sha256": b.docx_sha256,
        "pdf_sha256": b.pdf_sha256,
        "docx_size_bytes": b.docx_size_bytes,
        "pdf_size_bytes": b.pdf_size_bytes,
        "generated_by_email": b.generated_by.email,
        "generated_at": b.generated_at,
        "completed_at": b.completed_at,
    }


def _audit_row(a: AuditLog) -> dict:
    return {
        "id": a.pk,
        "action": a.action,
        "actor_email": a.actor.email if a.actor else None,
        "target_model": a.target_content_type.model if a.target_content_type else None,
        "target_object_id": a.target_object_id,
        "diff": a.diff,
        "metadata": a.metadata,
        "ip_address": a.ip_address,
        "created_at": a.created_at,
    }


def _output_dir(case: Case) -> Path:
    base = Path(settings.MEDIA_ROOT) / "archives" / case.case_id
    base.mkdir(parents=True, exist_ok=True)
    return base


def _audit_entries_for_case(case: Case):
    """All audit log entries whose target IS the case, plus those tagged in
    metadata.case_id (rare). Children's audit rows are reachable via the
    timeline endpoint; the archive captures everything that mentions the case
    directly in the manifest for the simplest seal story."""
    direct = AuditLog.objects.for_target(case)
    meta_tagged = AuditLog.objects.filter(metadata__case_id=case.case_id)
    return (direct | meta_tagged).distinct().order_by("created_at")


def archive_case(case: Case, archived_by) -> ArchiveRecord:
    """Build manifest, persist to disk, create ArchiveRecord. Synchronous.

    Raises if any step fails. The ArchiveRecord is only written after the
    manifest file exists on disk — never a half-archived state.
    """
    if hasattr(case, "archive_record"):
        raise RuntimeError(f"Case {case.case_id} is already archived.")

    archived_at = timezone.now()
    retention_until = archived_at + timedelta(days=DEFAULT_RETENTION_YEARS * 365)

    archived_by_payload = {
        "email": archived_by.email,
        "name": archived_by.full_name or archived_by.email,
    }

    manifest = engine.build_manifest(
        case_meta=_case_meta(case),
        archived_at=archived_at,
        archived_by=archived_by_payload,
        retention_until=retention_until,
        cea_results=[_cea_row(r) for r in case.cea_results.all().order_by("computed_at")],
        bia_results=[_bia_row(r) for r in case.bia_results.all().order_by("computed_at")],
        etd_appraisals=[
            _etd_row(a)
            for a in case.etd_appraisals.select_related("domain", "member").order_by("pk")
        ],
        references=[_reference_row(r) for r in case.references.all().order_by("pk")],
        recommendations=[
            _recommendation_row(r) for r in case.recommendations.all().order_by("computed_at")
        ],
        approvals=[
            _approval_row(a)
            for a in case.approvals.select_related("approver").order_by("signed_at")
        ],
        case_versions=[
            _case_version_row(v)
            for v in case.versions.select_related("locked_by").order_by("created_at")
        ],
        policy_briefs=[
            _policy_brief_row(b)
            for b in case.policy_briefs.select_related("generated_by").order_by("version")
        ],
        audit_log=[
            _audit_row(a) for a in _audit_entries_for_case(case).select_related("actor", "target_content_type")
        ],
    )

    manifest_bytes_value = engine.manifest_bytes(manifest)
    manifest_sha = engine.manifest_sha256(manifest)

    out_dir = _output_dir(case)
    manifest_path = out_dir / "manifest.json"
    manifest_path.write_bytes(manifest_bytes_value)

    rel_path = str(manifest_path.relative_to(settings.MEDIA_ROOT)).replace(os.sep, "/")

    artifact_counts = {
        "cea_results": len(manifest["artifacts"]["cea_results"]),
        "bia_results": len(manifest["artifacts"]["bia_results"]),
        "etd_appraisals": len(manifest["artifacts"]["etd_appraisals"]),
        "references": len(manifest["artifacts"]["references"]),
        "recommendations": len(manifest["artifacts"]["recommendations"]),
        "approvals": len(manifest["artifacts"]["approvals"]),
        "case_versions": len(manifest["artifacts"]["case_versions"]),
        "policy_briefs": len(manifest["artifacts"]["policy_briefs"]),
        "audit_log_entries": len(manifest["audit_log"]),
    }

    return ArchiveRecord.objects.create(
        case=case,
        archived_at=archived_at,
        archived_by=archived_by,
        manifest_path=rel_path,
        manifest_sha256=manifest_sha,
        manifest_size_bytes=len(manifest_bytes_value),
        retention_until=retention_until,
        artifact_counts=artifact_counts,
    )


def absolute_path(relative_media_path: str) -> Path:
    return Path(settings.MEDIA_ROOT) / relative_media_path
