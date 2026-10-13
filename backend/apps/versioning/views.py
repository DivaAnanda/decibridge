"""Versioning + audit-reconstruction endpoints.

  GET /api/v1/cases/{case_id}/versions/                       — list versions
  GET /api/v1/cases/{case_id}/versions/{version_id}/timeline/ — events up to this snapshot
  GET /api/v1/cases/{case_id}/versions/{version_id}/state/    — reconstructed state
  GET /api/v1/cases/{case_id}/versions/diff/?from=A&to=B      — field-level diff

All read-only. Append-only invariants on CaseVersion + AuditLog mean the
returned data is always reproducible bit-for-bit.
"""

from __future__ import annotations

from decimal import Decimal
from typing import Any

from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.approval.models import Approval
from apps.audit.models import AuditLog
from apps.bia.models import BIAResult
from apps.cases.models import Case, CaseVersion
from apps.cea.models import CEAResult
from apps.core.privacy import mask_ip, may_see_full_ip
from apps.policy_brief.models import PolicyBriefDocument
from apps.recommendation.models import Recommendation

from .permissions import VersioningPermission
from .serializers import AuditLogEntrySerializer, CaseVersionListSerializer


def _get_case(case_id: str) -> Case:
    return get_object_or_404(Case, case_id=case_id)


def _get_version(case: Case, version_id: int) -> CaseVersion:
    return get_object_or_404(CaseVersion, pk=version_id, case=case)


def _decimal_to_str(value: Any) -> Any:
    """JSON-safe: Decimals to strings, datetimes to ISO."""
    if isinstance(value, Decimal):
        return str(value)
    return value


# ----------------------------------------------------------------------------
# List
# ----------------------------------------------------------------------------


class VersionListView(APIView):
    """GET /api/v1/cases/{case_id}/versions/ — list all versions, newest first."""

    permission_classes = (IsAuthenticated, VersioningPermission)

    def get(self, request: Request, case_id: str) -> Response:
        case = _get_case(case_id)
        versions = (
            case.versions.select_related("locked_by", "created_by")
            .order_by("-created_at")
        )
        return Response(CaseVersionListSerializer(versions, many=True).data)


# ----------------------------------------------------------------------------
# Timeline — chronological audit log up to this snapshot's timestamp
# ----------------------------------------------------------------------------


class VersionTimelineView(APIView):
    """Returns AuditLog entries for this case, ordered oldest first, up to and
    including the snapshot's `created_at` (or `locked_at` if set)."""

    permission_classes = (IsAuthenticated, VersioningPermission)

    def get(self, request: Request, case_id: str, version_id: int) -> Response:
        case = _get_case(case_id)
        version = _get_version(case, version_id)

        snapshot_ts = version.locked_at or version.created_at

        # All audit log entries for this case (any model whose target is the case
        # itself, plus any whose target belongs to this case's children).
        # Simple approach: filter by `metadata.case_id` if present, plus direct
        # targets on the case.
        entries = AuditLog.objects.filter(
            created_at__lte=snapshot_ts,
        ).order_by("created_at")

        # Narrow by case: we look at both direct-target and metadata-tagged entries.
        case_entries = entries.for_target(case)
        # Also include entries where the target is a child object that belongs
        # to the case (CEA/BIA/EtD/Recommendation/Approval/PolicyBrief). We
        # determine this by checking metadata.case_id or target chain. For the
        # MVP we keep it simple and surface everything tagged with this case in
        # metadata.
        meta_tagged = entries.filter(metadata__case_id=case.case_id)

        combined = (case_entries | meta_tagged).distinct().order_by("created_at")

        return Response(
            AuditLogEntrySerializer(
                combined, many=True, context={"request": request}
            ).data
        )


# ----------------------------------------------------------------------------
# Snapshot state — reconstructed view of the case at this version
# ----------------------------------------------------------------------------


class VersionStateView(APIView):
    """Reconstruct what the KFT saw at the moment of this snapshot.

    Uses the soft pointers (cea_result_id, bia_result_id, recommendation_id,
    approval_id, policy_brief_document_id) on CaseVersion. Because every
    target table is append-only, the row referenced by ID is identical to
    what it was at snapshot time — no historical replay needed.
    """

    permission_classes = (IsAuthenticated, VersioningPermission)

    def get(self, request: Request, case_id: str, version_id: int) -> Response:
        case = _get_case(case_id)
        version = _get_version(case, version_id)

        payload: dict[str, Any] = {
            "version_number": version.version_number,
            "status": version.status,
            "trigger": version.trigger,
            "locked_at": version.locked_at,
            "locked_by": (
                version.locked_by.email if version.locked_by else None
            ),
            "lock_reason": version.lock_reason,
            **_state_blocks(version, request.user),
            # Phase V2: the full immutable value snapshot taken at lock time,
            # from which the economic blocks above are read.
            "snapshot": version.snapshot,
            "has_snapshot": version.snapshot is not None,
        }
        return Response(payload)


_DETERMINISTIC_FIELDS = (
    "total_cost_intervention",
    "total_cost_comparator",
    "total_qaly_intervention",
    "total_qaly_comparator",
    "incremental_cost",
    "incremental_qaly",
    "icer",
    "inb",
    "nmb_intervention",
    "nmb_comparator",
    "wtp_threshold_used",
    "decision_code",
    "algorithm_version",
    "computed_at",
)
_BIA_FIELDS = (
    "cumulative_net_impact",
    "pct_of_total_baseline",
    "annual_budget_baseline",
    "severity",
    "budget_score",
    "algorithm_version",
    "computed_at",
)
_PSA_FIELDS = (
    "n_simulations",
    "random_seed",
    "wtp_base",
    "prob_cost_effective_base",
    "mean_incremental_cost",
    "mean_incremental_qaly",
    "algorithm_version",
    "computed_at",
)


def _money(value: Any) -> Any:
    """The engine's per-year rows carry twenty decimal places; show four."""
    try:
        return str(Decimal(str(value)).quantize(Decimal("0.0001")))
    except (ArithmeticError, ValueError):
        return value


def _pick(block: dict | None, fields: tuple[str, ...]) -> dict | None:
    return {f: block.get(f) for f in fields} if block else None


def _state_blocks(version: CaseVersion, user) -> dict[str, dict | None]:
    """The headline figures of a version, shared by the state and diff views.

    Econ-first. A case built on apps.econ has no legacy CEAResult/BIAResult
    rows, so the pointer fields are empty and the screen said "Tidak ada data"
    for a locked case that plainly had both. Its figures are in the lock
    snapshot; the legacy pointers stay as the fallback for older versions.
    """
    snapshot = version.snapshot or {}
    econ = snapshot.get("econ") or {}

    bia = _pick(econ.get("bia"), _BIA_FIELDS)
    if bia is not None:
        for row in econ["bia"].get("per_year") or []:
            bia[f"net_impact_year_{row.get('year')}"] = _money(row.get("net_budget_impact"))

    cea = _pick(econ.get("deterministic"), _DETERMINISTIC_FIELDS)
    legacy_cea = _serialize_cea(version.cea_result_id)
    legacy_bia = _serialize_bia(version.bia_result_id)
    # A backfilled snapshot was rebuilt from whatever the case held at backfill
    # time, which can postdate the lock. Where the row the lock pointed at
    # still exists, that row is what the KFT saw.
    if snapshot.get("backfilled"):
        cea, bia = legacy_cea or cea, legacy_bia or bia

    return {
        "cea": cea or legacy_cea,
        "bia": bia or legacy_bia,
        "psa": _pick(econ.get("psa"), _PSA_FIELDS),
        "recommendation": _serialize_recommendation(version.recommendation_id),
        "approval": _serialize_approval(version.approval_id, user),
        "policy_brief": _serialize_policy_brief(version.policy_brief_document_id),
    }


def _serialize_cea(cea_id: int | None) -> dict | None:
    if cea_id is None:
        return None
    cea = CEAResult.objects.filter(pk=cea_id).first()
    if cea is None:
        return None
    return {
        "id": cea.pk,
        "icer_value": _decimal_to_str(cea.icer_value),
        "dominance": cea.dominance,
        "ce_score": cea.ce_score,
        "wtop_threshold": _decimal_to_str(cea.wtop_threshold_used),
        "sensitivity_low_icer": _decimal_to_str(cea.sensitivity_low_icer),
        "sensitivity_high_icer": _decimal_to_str(cea.sensitivity_high_icer),
        "computed_at": cea.computed_at,
        "algorithm_version": cea.algorithm_version,
    }


def _serialize_bia(bia_id: int | None) -> dict | None:
    if bia_id is None:
        return None
    bia = BIAResult.objects.filter(pk=bia_id).first()
    if bia is None:
        return None
    return {
        "id": bia.pk,
        "year1_net_impact": _decimal_to_str(bia.year1_net_impact),
        "year3_net_impact": _decimal_to_str(bia.year3_net_impact),
        "cumulative_impact": _decimal_to_str(bia.cumulative_impact),
        "pct_of_annual_budget": _decimal_to_str(bia.pct_of_annual_budget),
        "severity": bia.severity,
        "budget_score": bia.budget_score,
        "computed_at": bia.computed_at,
    }


def _serialize_recommendation(rec_id: int | None) -> dict | None:
    if rec_id is None:
        return None
    rec = Recommendation.objects.filter(pk=rec_id).first()
    if rec is None:
        return None
    return {
        "id": rec.pk,
        "traffic_light": rec.traffic_light,
        "composite_score": _decimal_to_str(rec.composite_score),
        "evidence_strength_score": _decimal_to_str(rec.evidence_strength_score),
        "ce_score": _decimal_to_str(rec.ce_score),
        "budget_score": _decimal_to_str(rec.budget_score),
        "cba_score": _decimal_to_str(rec.cba_score),
        "cba_criteria_count": rec.cba_criteria_count,
        "cba_satisfied_count": rec.cba_satisfied_count,
        "justification_text": rec.justification_text,
        "algorithm_version": rec.algorithm_version,
        "computed_at": rec.computed_at,
    }


def _serialize_approval(approval_id: int | None, user) -> dict | None:
    if approval_id is None:
        return None
    a = Approval.objects.filter(pk=approval_id).select_related("approver").first()
    if a is None:
        return None
    return {
        "id": a.pk,
        "decision": a.decision,
        "approver_name": a.approver.full_name or a.approver.email,
        "approver_email": a.approver.email,
        "signed_at": a.signed_at,
        # Masked like every other screen: only Admin IT reads a full address.
        "ip_address": a.ip_address if may_see_full_ip(user) else mask_ip(a.ip_address),
        "reason": a.reason,
    }


def _serialize_policy_brief(brief_id: int | None) -> dict | None:
    if brief_id is None:
        return None
    b = PolicyBriefDocument.objects.filter(pk=brief_id).first()
    if b is None:
        return None
    return {
        "id": b.pk,
        "version": b.version,
        "status": b.status,
        "docx_sha256": b.docx_sha256,
        "pdf_sha256": b.pdf_sha256,
        "generated_at": b.generated_at,
    }


# ----------------------------------------------------------------------------
# Diff — field-level comparison between two versions
# ----------------------------------------------------------------------------


class VersionDiffView(APIView):
    """GET /api/v1/cases/{case_id}/versions/diff/?from=<id>&to=<id>

    Returns a flat dict of {field_path: {"from": x, "to": y}} for every field
    that differs across the headline blocks: CEA result, BIA result, recommendation,
    approval, policy brief.
    """

    permission_classes = (IsAuthenticated, VersioningPermission)

    _COMPARED_BLOCKS = ("cea", "bia", "psa", "recommendation", "approval", "policy_brief")

    def get(self, request: Request, case_id: str) -> Response:
        case = _get_case(case_id)

        try:
            from_id = int(request.query_params.get("from", ""))
            to_id = int(request.query_params.get("to", ""))
        except ValueError:
            return Response(
                {"detail": "Parameter 'from' dan 'to' wajib berisi ID versi numerik."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        v_from = _get_version(case, from_id)
        v_to = _get_version(case, to_id)

        state_from = _state_blocks(v_from, request.user)
        state_to = _state_blocks(v_to, request.user)

        diff = {}
        for block in self._COMPARED_BLOCKS:
            b_from = state_from.get(block) or {}
            b_to = state_to.get(block) or {}
            block_diff = self._diff_dicts(b_from, b_to)
            if block_diff:
                diff[block] = block_diff

        return Response(
            {
                "from_version": v_from.version_number,
                "to_version": v_to.version_number,
                "from_id": v_from.pk,
                "to_id": v_to.pk,
                "diff": diff,
            }
        )

    @staticmethod
    def _diff_dicts(a: dict, b: dict) -> dict:
        diff = {}
        all_keys = set(a.keys()) | set(b.keys())
        for k in all_keys:
            av, bv = a.get(k), b.get(k)
            if av != bv:
                diff[k] = {"from": av, "to": bv}
        return diff
