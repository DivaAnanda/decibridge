from __future__ import annotations

from decimal import Decimal

from django.db import transaction
from django.shortcuts import get_object_or_404
from rest_framework import generics, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.audit.middleware import client_ip
from apps.audit.models import AuditLog
from apps.bia.models import BIAResult
from apps.cases.models import Case
from apps.econ.models import EconDeterministicResult
from apps.econ.scoring import ce_score_from_result
from apps.etd.aggregation import aggregate_domain, aggregate_overall
from apps.etd.models import EtDAppraisal, EtDDomain

from .aggregation import aggregate_per_domain
from .engine import (
    ALGORITHM_VERSION,
    STATUS_INCOMPLETE,
    SynthesisInput,
    compute_recommendation,
)
from .models import CBACriterion, DomainWeightVote, Recommendation
from .permissions import CBAPermission, ComputePermission, WeightVotePermission
from .serializers import (
    CBACriterionSerializer,
    DomainWeightUpsertSerializer,
    DomainWeightVoteReadSerializer,
    RecommendationSerializer,
    WeightsSummarySerializer,
)


def _get_case(case_id: str) -> Case:
    return get_object_or_404(Case, case_id=case_id)


# ── Weights ──────────────────────────────────────────────────────────────


class WeightVoteListUpsertView(APIView):
    """GET: all votes on the case. POST: upsert caller's own row(s) in bulk."""

    permission_classes = (IsAuthenticated, WeightVotePermission)

    def get(self, request: Request, case_id: str) -> Response:
        case = _get_case(case_id)
        votes = DomainWeightVote.objects.filter(case=case).select_related("domain", "member")
        return Response(DomainWeightVoteReadSerializer(votes, many=True).data)

    def post(self, request: Request, case_id: str) -> Response:
        case = _get_case(case_id)
        if case.is_locked:
            return Response(
                {"detail": "Kasus terkunci — bobot tidak dapat diubah."},
                status=status.HTTP_403_FORBIDDEN,
            )
        serializer = DomainWeightUpsertSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        weights = serializer.validated_data["weights"]

        domains_by_slug = {d.slug: d for d in EtDDomain.objects.all()}
        unknown = set(weights.keys()) - set(domains_by_slug.keys())
        if unknown:
            return Response(
                {"weights": f"Slug domain tidak dikenal: {sorted(unknown)}"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        with transaction.atomic():
            for slug, weight in weights.items():
                DomainWeightVote.objects.update_or_create(
                    case=case,
                    domain=domains_by_slug[slug],
                    member=request.user,
                    defaults={"weight": weight},
                )

        votes = DomainWeightVote.objects.filter(case=case, member=request.user).select_related(
            "domain"
        )
        return Response(DomainWeightVoteReadSerializer(votes, many=True).data)


class WeightsSummaryView(APIView):
    """Aggregated weights across all members for the case."""

    permission_classes = (IsAuthenticated,)

    def get(self, request: Request, case_id: str) -> Response:
        case = _get_case(case_id)
        method = request.query_params.get("method", "mean")
        if method not in {"mean", "median"}:
            return Response({"method": "Harus 'mean' atau 'median'."}, status=400)

        domains = EtDDomain.objects.all().order_by("order")
        votes_by_slug: dict[str, list[int]] = {d.slug: [] for d in domains}
        for v in DomainWeightVote.objects.filter(case=case).select_related("domain"):
            votes_by_slug[v.domain.slug].append(v.weight)

        aggregates = aggregate_per_domain(votes_by_slug, method=method)
        # Preserve the canonical domain order
        ordered = [aggregates[d.slug] for d in domains]
        payload = {"method": method, "aggregates": [a.__dict__ for a in ordered]}
        return Response(WeightsSummarySerializer(payload).data)


# ── CBA ──────────────────────────────────────────────────────────────────


class CBACriterionListCreateView(generics.ListCreateAPIView):
    serializer_class = CBACriterionSerializer
    permission_classes = (IsAuthenticated, CBAPermission)
    pagination_class = None

    def get_queryset(self):
        return CBACriterion.objects.filter(case__case_id=self.kwargs["case_id"]).select_related(
            "created_by", "last_edited_by"
        )

    def perform_create(self, serializer):
        case = _get_case(self.kwargs["case_id"])
        if case.is_locked:
            from rest_framework.exceptions import PermissionDenied

            raise PermissionDenied("Kasus terkunci — kriteria CBA tidak dapat ditambahkan.")
        next_order = (
            CBACriterion.objects.filter(case=case)
            .order_by("-order")
            .values_list("order", flat=True)
            .first()
            or 0
        ) + 1
        serializer.save(
            case=case,
            order=next_order,
            created_by=self.request.user,
            last_edited_by=self.request.user,
        )


class CBACriterionDetailView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = CBACriterionSerializer
    permission_classes = (IsAuthenticated, CBAPermission)

    def get_queryset(self):
        return CBACriterion.objects.filter(case__case_id=self.kwargs["case_id"])

    def perform_update(self, serializer):
        if serializer.instance.case.is_locked:
            from rest_framework.exceptions import PermissionDenied

            raise PermissionDenied("Kasus terkunci — kriteria CBA tidak dapat diubah.")
        serializer.save(last_edited_by=self.request.user)

    def perform_destroy(self, instance):
        if instance.case.is_locked:
            from rest_framework.exceptions import PermissionDenied

            raise PermissionDenied("Kasus terkunci — kriteria CBA tidak dapat dihapus.")
        instance.delete()


# ── Synthesis ─────────────────────────────────────────────────────────────


class RecommendationComputeView(APIView):
    """POST: pull latest CEA, BIA, EtD, CBA → run engine → append Recommendation row."""

    permission_classes = (IsAuthenticated, ComputePermission)

    def post(self, request: Request, case_id: str) -> Response:
        case = _get_case(case_id)
        if case.is_locked:
            return Response(
                {"detail": "Kasus terkunci — rekomendasi tidak dapat dihitung ulang."},
                status=status.HTTP_403_FORBIDDEN,
            )

        latest_econ: EconDeterministicResult | None = (
            case.econ_deterministic_results.order_by("-computed_at").first()
        )
        latest_bia: BIAResult | None = case.bia_results.order_by("-computed_at").first()

        domains = list(EtDDomain.objects.all().order_by("order"))
        appraisals_by_domain: dict[int, list[EtDAppraisal]] = {d.pk: [] for d in domains}
        for a in EtDAppraisal.objects.filter(case=case).only(
            "judgement", "certainty", "domain_id"
        ):
            appraisals_by_domain[a.domain_id].append(a)
        per_domain = [aggregate_domain(d.slug, appraisals_by_domain[d.pk]) for d in domains]
        overall = aggregate_overall(per_domain, total_domains=len(domains))

        cba_criteria = list(case.cba_criteria.all())
        cba_satisfied = sum(1 for c in cba_criteria if c.is_satisfied)

        method = request.data.get("weight_aggregation_method", "mean")
        if method not in {"mean", "median"}:
            method = "mean"

        synth_input = SynthesisInput(
            evidence_strength_score=overall.evidence_strength_score,
            ce_score=(ce_score_from_result(latest_econ) if latest_econ else None),
            budget_score=(Decimal(latest_bia.budget_score) if latest_bia else None),
            cba_criteria_count=len(cba_criteria),
            cba_satisfied_count=cba_satisfied,
        )
        synth = compute_recommendation(synth_input)

        # R3: do not persist / do not fabricate a RED when inputs are incomplete.
        if synth.status == STATUS_INCOMPLETE:
            return Response(
                {
                    "detail": synth.justification_text,
                    "missing_components": synth.missing_components,
                },
                status=status.HTTP_422_UNPROCESSABLE_ENTITY,
            )

        snapshot = {
            "synthesis_input": synth_input.snapshot(),
            "econ_result_id": latest_econ.pk if latest_econ else None,
            "bia_result_id": latest_bia.pk if latest_bia else None,
            "etd_domains_completed": overall.domains_completed,
            "etd_domains_total": overall.domains_total,
            "cba_criteria": [
                {
                    "id": c.pk,
                    "criterion_name": c.criterion_name,
                    "is_satisfied": c.is_satisfied,
                }
                for c in cba_criteria
            ],
            "weight_aggregation_method": method,
        }

        rec = Recommendation.objects.create(
            case=case,
            input_snapshot=snapshot,
            evidence_strength_score=synth.evidence_strength_score,
            ce_score=synth.ce_score,
            budget_score=synth.budget_score,
            cba_score=synth.cba_score,
            composite_score=synth.composite_score,
            traffic_light=synth.traffic_light,
            justification_text=synth.justification_text,
            cba_criteria_count=synth.cba_criteria_count,
            cba_satisfied_count=synth.cba_satisfied_count,
            algorithm_version=ALGORITHM_VERSION,
            weight_aggregation_method=method,
            computed_by=request.user,
        )

        AuditLog.record(
            action=AuditLog.Action.UPDATE,
            actor=request.user,
            target=case,
            diff={
                "recommendation": {
                    "old": None,
                    "new": {
                        "traffic_light": synth.traffic_light,
                        "composite_score": str(synth.composite_score),
                    },
                }
            },
            metadata={
                "recommendation_id": rec.pk,
                "algorithm_version": ALGORITHM_VERSION,
            },
            ip=client_ip(request),
            user_agent=request.META.get("HTTP_USER_AGENT", "")[:512],
        )

        return Response(RecommendationSerializer(rec).data, status=status.HTTP_201_CREATED)


class RecommendationListView(APIView):
    permission_classes = (IsAuthenticated,)

    def get(self, request: Request, case_id: str) -> Response:
        case = _get_case(case_id)
        recs = case.recommendations.all().select_related("computed_by")
        return Response(RecommendationSerializer(recs, many=True).data)


class RecommendationLatestView(APIView):
    permission_classes = (IsAuthenticated,)

    def get(self, request: Request, case_id: str) -> Response:
        case = _get_case(case_id)
        latest = case.recommendations.order_by("-computed_at").first()
        if latest is None:
            return Response(None, status=status.HTTP_204_NO_CONTENT)
        return Response(RecommendationSerializer(latest).data)
