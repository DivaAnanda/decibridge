from __future__ import annotations

from django.http import FileResponse, Http404
from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.audit.middleware import client_ip
from apps.audit.models import AuditLog
from apps.cases.models import Case, CaseStatus
from apps.recommendation.models import Recommendation

from . import service
from .models import GenerationStatus, PolicyBriefDocument
from .permissions import PolicyBriefPermission
from .serializers import PolicyBriefDocumentSerializer


def _get_case(case_id: str) -> Case:
    return get_object_or_404(Case, case_id=case_id)


def _get_brief(case: Case, brief_id: int) -> PolicyBriefDocument:
    return get_object_or_404(PolicyBriefDocument, pk=brief_id, case=case)


# ----------------------------------------------------------------------------
# List + generate
# ----------------------------------------------------------------------------


class PolicyBriefListGenerateView(APIView):
    """GET   /api/v1/cases/{case_id}/policy-briefs/        — list all versions.
    POST  /api/v1/cases/{case_id}/policy-briefs/         — generate v(N+1).
    """

    permission_classes = (IsAuthenticated, PolicyBriefPermission)

    def get(self, request: Request, case_id: str) -> Response:
        case = _get_case(case_id)
        briefs = PolicyBriefDocument.objects.filter(case=case).order_by("-version")
        return Response(PolicyBriefDocumentSerializer(briefs, many=True).data)

    def post(self, request: Request, case_id: str) -> Response:
        case = _get_case(case_id)

        # Gate: case must be approved or locked.
        if case.status not in {CaseStatus.APPROVED, CaseStatus.LOCKED}:
            return Response(
                {
                    "detail": (
                        "Ringkasan kebijakan hanya dapat diterbitkan setelah kasus "
                        f"disetujui atau dikunci (status saat ini: {case.status})."
                    )
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Gate: case must have a computed recommendation.
        latest_rec = (
            Recommendation.objects.filter(case=case).order_by("-computed_at").first()
        )
        if latest_rec is None:
            return Response(
                {"detail": "Belum ada rekomendasi untuk kasus ini. Hitung rekomendasi terlebih dahulu."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Refuse to start a new run while another is still mid-generation.
        if PolicyBriefDocument.objects.filter(
            case=case, status=GenerationStatus.GENERATING
        ).exists():
            return Response(
                {"detail": "Ada proses pembuatan dokumen yang masih berjalan. Tunggu sampai selesai."},
                status=status.HTTP_409_CONFLICT,
            )

        try:
            doc = service.generate_brief(
                case=case,
                generated_by=request.user,
                source_recommendation=latest_rec,
            )
        except Exception as exc:  # pragma: no cover — surfaced to client
            return Response(
                {"detail": f"Pembuatan dokumen gagal: {exc}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        AuditLog.record(
            action=AuditLog.Action.CREATE,
            actor=request.user,
            target=case,
            diff={
                "policy_brief": {
                    "old": None,
                    "new": {
                        "version": doc.version,
                        "docx_sha256": doc.docx_sha256,
                        "pdf_sha256": doc.pdf_sha256,
                    },
                }
            },
            metadata={
                "policy_brief_id": doc.pk,
                "source_recommendation_id": latest_rec.pk,
            },
            ip=client_ip(request),
            user_agent=request.META.get("HTTP_USER_AGENT", "")[:512],
        )

        return Response(
            PolicyBriefDocumentSerializer(doc).data, status=status.HTTP_201_CREATED
        )


# ----------------------------------------------------------------------------
# Detail + download
# ----------------------------------------------------------------------------


class PolicyBriefDetailView(APIView):
    """GET /api/v1/cases/{case_id}/policy-briefs/{id}/   — single doc metadata."""

    permission_classes = (IsAuthenticated, PolicyBriefPermission)

    def get(self, request: Request, case_id: str, brief_id: int) -> Response:
        case = _get_case(case_id)
        doc = _get_brief(case, brief_id)
        return Response(PolicyBriefDocumentSerializer(doc).data)


class PolicyBriefDownloadView(APIView):
    """GET /api/v1/cases/{case_id}/policy-briefs/{id}/download/{format}/

    format ∈ {docx, pdf}.
    Streams the file with the original case_id + version in the filename.
    """

    permission_classes = (IsAuthenticated, PolicyBriefPermission)

    def get(
        self, request: Request, case_id: str, brief_id: int, fmt: str
    ) -> FileResponse | Response:
        case = _get_case(case_id)
        doc = _get_brief(case, brief_id)

        if doc.status != GenerationStatus.COMPLETED:
            return Response(
                {"detail": f"Dokumen belum siap (status: {doc.status})."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        fmt = fmt.lower()
        if fmt == "docx":
            rel_path, content_type = doc.docx_path, (
                "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
            )
        elif fmt == "pdf":
            rel_path, content_type = doc.pdf_path, "application/pdf"
        else:
            return Response(
                {"detail": "Format tidak dikenal. Gunakan 'docx' atau 'pdf'."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if not rel_path:
            raise Http404("File path missing on document row.")

        abs_path = service.absolute_path(rel_path)
        if not abs_path.exists():
            raise Http404(f"File missing on disk: {rel_path}")

        filename = f"{case.case_id}_policy_brief_v{doc.version}.{fmt}"
        response = FileResponse(
            open(abs_path, "rb"), content_type=content_type, as_attachment=True, filename=filename
        )
        return response
