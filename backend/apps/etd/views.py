from __future__ import annotations

from django.db.models import Prefetch
from django.shortcuts import get_object_or_404
from rest_framework import generics, status, viewsets
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.audit.middleware import client_ip
from apps.audit.models import AuditLog
from apps.cases.models import Case

from .aggregation import aggregate_domain, aggregate_overall
from .models import EtDAppraisal, EtDDomain, ReferenceCitation
from .permissions import (
    EtDAppraisalPermission,
    ReferencePermission,
)
from .serializers import (
    EtDAppraisalReadSerializer,
    EtDAppraisalWriteSerializer,
    EtDDomainSerializer,
    EtDSummarySerializer,
    ReferenceCitationSerializer,
)


def _get_case(case_id: str) -> Case:
    return get_object_or_404(Case, case_id=case_id)


class EtDDomainListView(generics.ListAPIView):
    """Read-only: the 9 seeded domains."""

    queryset = EtDDomain.objects.all().order_by("order")
    serializer_class = EtDDomainSerializer
    permission_classes = (IsAuthenticated,)
    pagination_class = None


class ReferenceListCreateView(generics.ListCreateAPIView):
    serializer_class = ReferenceCitationSerializer
    permission_classes = (IsAuthenticated, ReferencePermission)
    pagination_class = None

    def get_queryset(self):
        return ReferenceCitation.objects.filter(case__case_id=self.kwargs["case_id"]).select_related(
            "created_by"
        )

    def perform_create(self, serializer):
        case = _get_case(self.kwargs["case_id"])
        if case.is_locked:
            from rest_framework.exceptions import PermissionDenied

            raise PermissionDenied("Kasus terkunci — tidak dapat menambah referensi.")
        serializer.save(case=case, created_by=self.request.user)


class ReferenceDetailView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = ReferenceCitationSerializer
    permission_classes = (IsAuthenticated, ReferencePermission)
    lookup_field = "pk"

    def get_queryset(self):
        return ReferenceCitation.objects.filter(case__case_id=self.kwargs["case_id"])

    def perform_update(self, serializer):
        if serializer.instance.case.is_locked:
            from rest_framework.exceptions import PermissionDenied

            raise PermissionDenied("Kasus terkunci — referensi tidak dapat diubah.")
        serializer.save()

    def perform_destroy(self, instance):
        if instance.case.is_locked:
            from rest_framework.exceptions import PermissionDenied

            raise PermissionDenied("Kasus terkunci — referensi tidak dapat dihapus.")
        instance.delete()


class EtDAppraisalListCreateView(APIView):
    """GET list of all appraisals on a case; POST upserts the caller's own
    appraisal for a given domain (so multiple POSTs by the same member +
    same domain don't error out, they just update)."""

    permission_classes = (IsAuthenticated, EtDAppraisalPermission)

    def get(self, request: Request, case_id: str) -> Response:
        case = _get_case(case_id)
        appraisals = (
            EtDAppraisal.objects.filter(case=case)
            .select_related("domain", "member")
            .prefetch_related("references")
            .order_by("domain__order", "member__email")
        )
        return Response(EtDAppraisalReadSerializer(appraisals, many=True).data)

    def post(self, request: Request, case_id: str) -> Response:
        case = _get_case(case_id)
        if case.is_locked:
            return Response(
                {"detail": "Kasus terkunci — appraisal tidak dapat diubah."},
                status=status.HTTP_403_FORBIDDEN,
            )

        domain_slug = request.data.get("domain_slug")
        if not domain_slug:
            return Response({"domain_slug": "Wajib diisi."}, status=status.HTTP_400_BAD_REQUEST)
        domain = get_object_or_404(EtDDomain, slug=domain_slug)

        serializer = EtDAppraisalWriteSerializer(
            data=request.data, context={"case": case, "request": request}
        )
        serializer.is_valid(raise_exception=True)

        instance, created = EtDAppraisal.objects.update_or_create(
            case=case,
            domain=domain,
            member=request.user,
            defaults={
                "judgement": serializer.validated_data["judgement"],
                "certainty": serializer.validated_data.get("certainty", "moderate"),
                "narrative": serializer.validated_data.get("narrative", ""),
            },
        )
        # M2M is set after the row exists.
        refs = serializer.validated_data.get("references") or []
        instance.references.set(refs)

        AuditLog.record(
            action=AuditLog.Action.UPDATE,
            actor=request.user,
            target=case,
            diff={
                f"etd_appraisal:{domain.slug}": {
                    "old": None if created else "updated",
                    "new": {
                        "judgement": instance.judgement,
                        "certainty": instance.certainty,
                        "member": request.user.email,
                    },
                }
            },
            metadata={"domain_slug": domain.slug, "appraisal_id": instance.pk},
            ip=client_ip(request),
            user_agent=request.META.get("HTTP_USER_AGENT", "")[:512],
        )

        return Response(
            EtDAppraisalReadSerializer(instance).data,
            status=status.HTTP_201_CREATED if created else status.HTTP_200_OK,
        )


class EtDAppraisalDeleteView(APIView):
    """A KFT member may withdraw their own appraisal for one domain."""

    permission_classes = (IsAuthenticated, EtDAppraisalPermission)

    def delete(self, request: Request, case_id: str, domain_slug: str) -> Response:
        case = _get_case(case_id)
        instance = get_object_or_404(
            EtDAppraisal, case=case, domain__slug=domain_slug, member=request.user
        )
        self.check_object_permissions(request, instance)
        instance.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class EtDSummaryView(APIView):
    """Aggregate per-domain + overall evidence-strength score."""

    permission_classes = (IsAuthenticated,)

    def get(self, request: Request, case_id: str) -> Response:
        case = _get_case(case_id)
        domains = list(EtDDomain.objects.all().order_by("order"))
        per_domain = []
        appraisals_by_domain: dict[int, list[EtDAppraisal]] = {d.pk: [] for d in domains}
        for a in (
            EtDAppraisal.objects.filter(case=case).select_related("domain").only(
                "judgement", "certainty", "domain_id"
            )
        ):
            appraisals_by_domain[a.domain_id].append(a)
        for d in domains:
            per_domain.append(aggregate_domain(d.slug, appraisals_by_domain[d.pk]))
        overall = aggregate_overall(per_domain, total_domains=len(domains))

        payload = {
            "per_domain": [d.__dict__ for d in per_domain],
            "overall": overall.__dict__,
        }
        return Response(EtDSummarySerializer(payload).data)
