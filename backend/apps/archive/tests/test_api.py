from __future__ import annotations

import json
from datetime import timedelta
from pathlib import Path

import pytest
from django.conf import settings
from rest_framework import status

from apps.archive.models import DEFAULT_RETENTION_YEARS, ArchiveRecord


def _detail_url(case_id: str) -> str:
    return f"/api/v1/cases/{case_id}/archive/"


def _manifest_url(case_id: str) -> str:
    return f"/api/v1/cases/{case_id}/archive/manifest/"


# ----------------------------------------------------------------------------
# Auto-archive on state machine transition
# ----------------------------------------------------------------------------


@pytest.mark.django_db
class TestAutoArchive:
    def test_archive_transition_creates_record(self, archived_case):
        assert ArchiveRecord.objects.filter(case=archived_case).count() == 1
        record = ArchiveRecord.objects.get(case=archived_case)
        assert record.manifest_sha256
        assert record.manifest_path
        assert record.manifest_size_bytes > 0

    def test_manifest_file_written_to_disk(self, archived_case):
        record = ArchiveRecord.objects.get(case=archived_case)
        path = Path(settings.MEDIA_ROOT) / record.manifest_path
        assert path.exists()
        assert path.stat().st_size == record.manifest_size_bytes

    def test_manifest_is_valid_json(self, archived_case):
        record = ArchiveRecord.objects.get(case=archived_case)
        path = Path(settings.MEDIA_ROOT) / record.manifest_path
        data = json.loads(path.read_text(encoding="utf-8"))
        assert data["schema_version"] == "1.0"
        assert data["case_id"] == archived_case.case_id

    def test_manifest_lists_artifacts_with_per_row_hashes(self, archived_case):
        record = ArchiveRecord.objects.get(case=archived_case)
        path = Path(settings.MEDIA_ROOT) / record.manifest_path
        data = json.loads(path.read_text(encoding="utf-8"))
        recs = data["artifacts"]["recommendations"]
        assert len(recs) >= 1
        for r in recs:
            assert "sha256" in r
            assert len(r["sha256"]) == 64

    def test_artifact_counts_populated(self, archived_case):
        record = ArchiveRecord.objects.get(case=archived_case)
        assert record.artifact_counts["recommendations"] >= 1
        assert record.artifact_counts["case_versions"] >= 1  # lock created v1.0

    def test_retention_until_is_seven_years_out(self, archived_case):
        record = ArchiveRecord.objects.get(case=archived_case)
        delta = record.retention_until - record.archived_at
        assert delta == timedelta(days=DEFAULT_RETENTION_YEARS * 365)


# ----------------------------------------------------------------------------
# Append-only invariants
# ----------------------------------------------------------------------------


@pytest.mark.django_db
class TestImmutability:
    def test_cannot_update_archive_record(self, archived_case):
        record = ArchiveRecord.objects.get(case=archived_case)
        record.notes = "tampered"
        with pytest.raises(PermissionError):
            record.save()

    def test_cannot_delete_archive_record(self, archived_case):
        record = ArchiveRecord.objects.get(case=archived_case)
        with pytest.raises(PermissionError):
            record.delete()


# ----------------------------------------------------------------------------
# Role gate on archive ACTION (via state machine)
# ----------------------------------------------------------------------------


@pytest.mark.django_db
class TestArchiveActionGates:
    def test_hta_cannot_archive(self, locked_case, hta_user):
        from django.core.exceptions import PermissionDenied

        from apps.cases.state_machine import transition as case_transition

        with pytest.raises(PermissionDenied):
            case_transition(locked_case, "archive", hta_user)

    def test_kft_member_cannot_archive(self, locked_case, kft_member_user):
        from django.core.exceptions import PermissionDenied

        from apps.cases.state_machine import transition as case_transition

        with pytest.raises(PermissionDenied):
            case_transition(locked_case, "archive", kft_member_user)


# ----------------------------------------------------------------------------
# API endpoints — list/detail/download
# ----------------------------------------------------------------------------


@pytest.mark.django_db
class TestArchiveDetailAPI:
    def test_get_returns_record_for_archived_case(self, hta_client, archived_case):
        response = hta_client.get(_detail_url(archived_case.case_id))
        assert response.status_code == status.HTTP_200_OK
        assert response.data["case_id"] == archived_case.case_id
        assert response.data["manifest_sha256"]
        assert response.data["retention_until"]

    def test_get_returns_404_for_unarchived_case(self, hta_client, locked_case):
        response = hta_client.get(_detail_url(locked_case.case_id))
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_kft_member_can_read(self, kft_member_client, archived_case):
        response = kft_member_client.get(_detail_url(archived_case.case_id))
        assert response.status_code == status.HTTP_200_OK

    def test_unauthenticated_blocked(self, api_client, archived_case):
        response = api_client.get(_detail_url(archived_case.case_id))
        assert response.status_code == status.HTTP_401_UNAUTHORIZED


@pytest.mark.django_db
class TestManifestDownload:
    def test_download_returns_json(self, hta_client, archived_case):
        response = hta_client.get(_manifest_url(archived_case.case_id))
        assert response.status_code == status.HTTP_200_OK
        assert response["Content-Type"] == "application/json"
        assert "archive_manifest.json" in response["Content-Disposition"]

    def test_download_404_for_unarchived(self, hta_client, locked_case):
        response = hta_client.get(_manifest_url(locked_case.case_id))
        assert response.status_code == status.HTTP_404_NOT_FOUND
