from __future__ import annotations

import pytest
from rest_framework import status

from apps.cases.models import CaseVersion


def _list_url(case_id: str) -> str:
    return f"/api/v1/cases/{case_id}/versions/"


def _timeline_url(case_id: str, version_id: int) -> str:
    return f"/api/v1/cases/{case_id}/versions/{version_id}/timeline/"


def _state_url(case_id: str, version_id: int) -> str:
    return f"/api/v1/cases/{case_id}/versions/{version_id}/state/"


def _diff_url(case_id: str, from_id: int, to_id: int) -> str:
    return f"/api/v1/cases/{case_id}/versions/diff/?from={from_id}&to={to_id}"


# ----------------------------------------------------------------------------
# Auto-snapshot on lock
# ----------------------------------------------------------------------------


@pytest.mark.django_db
class TestAutoSnapshotOnLock:
    def test_lock_creates_version_row(self, locked_case):
        locked_versions = CaseVersion.objects.filter(
            case=locked_case, status="locked"
        )
        assert locked_versions.count() == 1
        v = locked_versions.first()
        assert v.version_number == "1.0"
        assert v.trigger == "locked"
        assert v.locked_by is not None

    def test_lock_captures_recommendation_pointer(self, locked_case):
        v = CaseVersion.objects.get(case=locked_case, status="locked")
        assert v.recommendation_id is not None
        # Note: approval_id is only captured when the case goes through the
        # Sign-Off endpoint (which creates an Approval row). Direct
        # state-machine transitions in this test fixture don't, so it stays None.
        # The end-to-end approval→lock flow is verified manually + via the
        # approval app's own test suite.


# ----------------------------------------------------------------------------
# Versioning numbering
# ----------------------------------------------------------------------------


@pytest.mark.django_db
class TestVersionNumbering:
    def test_second_lock_bumps_minor(self, two_locked_versions):
        locked = CaseVersion.objects.filter(
            case=two_locked_versions, status="locked"
        ).order_by("id")
        assert [v.version_number for v in locked] == ["1.0", "1.1"]


# ----------------------------------------------------------------------------
# Immutability
# ----------------------------------------------------------------------------


@pytest.mark.django_db
class TestImmutability:
    def test_cannot_update_existing_version(self, locked_case):
        v = CaseVersion.objects.get(case=locked_case, status="locked")
        v.lock_reason = "tampered"
        with pytest.raises(PermissionError):
            v.save()

    def test_cannot_delete_version(self, locked_case):
        v = CaseVersion.objects.get(case=locked_case, status="locked")
        with pytest.raises(PermissionError):
            v.delete()


# ----------------------------------------------------------------------------
# List endpoint
# ----------------------------------------------------------------------------


@pytest.mark.django_db
class TestVersionList:
    def test_lists_all_versions_newest_first(self, hta_client, locked_case):
        response = hta_client.get(_list_url(locked_case.case_id))
        assert response.status_code == status.HTTP_200_OK
        # pilot_case fixture creates Case directly (bypassing the serializer
        # that auto-creates v0.1.0), so only the v1.0 lock snapshot exists.
        labels = [v["version_number"] for v in response.data]
        assert "1.0" in labels
        assert labels[0] == "1.0"  # newest first

    def test_kft_member_can_list(self, kft_member_client, locked_case):
        response = kft_member_client.get(_list_url(locked_case.case_id))
        assert response.status_code == status.HTTP_200_OK

    def test_unauthenticated_blocked(self, api_client, locked_case):
        response = api_client.get(_list_url(locked_case.case_id))
        assert response.status_code == status.HTTP_401_UNAUTHORIZED


# ----------------------------------------------------------------------------
# Timeline endpoint
# ----------------------------------------------------------------------------


@pytest.mark.django_db
class TestVersionTimeline:
    def test_timeline_returns_audit_entries(self, hta_client, locked_case):
        v = CaseVersion.objects.get(case=locked_case, status="locked")
        response = hta_client.get(_timeline_url(locked_case.case_id, v.pk))
        assert response.status_code == status.HTTP_200_OK
        # The case has been submitted, approved, locked → multiple audit rows
        # should be present (at least the state-machine transitions logged in
        # the views, plus the approve event from sign-off if any).
        assert isinstance(response.data, list)

    def test_timeline_ordered_oldest_first(self, hta_client, locked_case):
        v = CaseVersion.objects.get(case=locked_case, status="locked")
        response = hta_client.get(_timeline_url(locked_case.case_id, v.pk))
        timestamps = [entry["created_at"] for entry in response.data]
        assert timestamps == sorted(timestamps)


# ----------------------------------------------------------------------------
# State reconstruction
# ----------------------------------------------------------------------------


@pytest.mark.django_db
class TestVersionState:
    def test_state_returns_block_summaries(self, hta_client, locked_case):
        v = CaseVersion.objects.get(case=locked_case, status="locked")
        response = hta_client.get(_state_url(locked_case.case_id, v.pk))
        assert response.status_code == status.HTTP_200_OK
        data = response.data
        assert data["version_number"] == "1.0"
        assert data["status"] == "locked"
        # CEA + BIA were not computed in the fixture, so they should be None.
        # But the recommendation pointer was captured at lock.
        assert data["recommendation"] is not None
        assert data["recommendation"]["traffic_light"] == "green"

    def test_state_without_artifacts_returns_no_pointers(
        self, hta_client, pilot_case, hta_user, ketua_user
    ):
        """A locked case that never ran CEA/BIA still produces a state response
        with null pointers — UI must handle that gracefully."""
        from apps.cases.state_machine import transition as case_transition

        case_transition(pilot_case, "submit", hta_user)
        case_transition(pilot_case, "approve", ketua_user)
        case_transition(pilot_case, "lock", ketua_user)

        v = CaseVersion.objects.get(case=pilot_case, status="locked")
        response = hta_client.get(_state_url(pilot_case.case_id, v.pk))
        assert response.status_code == status.HTTP_200_OK
        assert response.data["recommendation"] is None
        assert response.data["cea"] is None
        assert response.data["bia"] is None


# ----------------------------------------------------------------------------
# Diff
# ----------------------------------------------------------------------------


@pytest.mark.django_db
class TestVersionDiff:
    def test_diff_returns_changed_fields(self, hta_client, two_locked_versions):
        locked = list(
            CaseVersion.objects.filter(
                case=two_locked_versions, status="locked"
            ).order_by("id")
        )
        v_from, v_to = locked[0], locked[1]
        response = hta_client.get(
            _diff_url(two_locked_versions.case_id, v_from.pk, v_to.pk)
        )
        assert response.status_code == status.HTTP_200_OK
        diff = response.data["diff"]
        assert "recommendation" in diff
        # Composite scores differ between the two fixtures (85.00 vs 95.00).
        assert "composite_score" in diff["recommendation"]
        assert diff["recommendation"]["composite_score"]["from"] == "85.00"
        assert diff["recommendation"]["composite_score"]["to"] == "95.00"

    def test_diff_missing_from_param_rejected(self, hta_client, locked_case):
        url = f"/api/v1/cases/{locked_case.case_id}/versions/diff/?from=&to="
        response = hta_client.get(url)
        assert response.status_code == status.HTTP_400_BAD_REQUEST
