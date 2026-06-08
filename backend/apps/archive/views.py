from __future__ import annotations

from django.http import FileResponse, Http404
from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.cases.models import Case

from . import service
from .models import ArchiveRecord
from .permissions import ArchivePermission
from .serializers import ArchiveRecordSerializer


def _get_case(case_id: str) -> Case:
    return get_object_or_404(Case, case_id=case_id)


class ArchiveDetailView(APIView):
    """GET /api/v1/cases/{case_id}/archive/ — the ArchiveRecord, if any.

    Returns 404 if the case isn't yet archived. The frontend can use that as
    a "show the Arsipkan button" signal.
    """

    permission_classes = (IsAuthenticated, ArchivePermission)

    def get(self, request: Request, case_id: str) -> Response:
        case = _get_case(case_id)
        record = get_object_or_404(ArchiveRecord, case=case)
        return Response(ArchiveRecordSerializer(record).data)


class ArchiveManifestDownloadView(APIView):
    """GET /api/v1/cases/{case_id}/archive/manifest/ — download manifest.json."""

    permission_classes = (IsAuthenticated, ArchivePermission)

    def get(self, request: Request, case_id: str) -> FileResponse | Response:
        case = _get_case(case_id)
        record = get_object_or_404(ArchiveRecord, case=case)

        if not record.manifest_path:
            return Response(
                {"detail": "Manifest file is missing from this archive record."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        abs_path = service.absolute_path(record.manifest_path)
        if not abs_path.exists():
            raise Http404(f"Manifest file missing on disk: {record.manifest_path}")

        return FileResponse(
            open(abs_path, "rb"),
            content_type="application/json",
            as_attachment=True,
            filename=f"{case.case_id}_archive_manifest.json",
        )
