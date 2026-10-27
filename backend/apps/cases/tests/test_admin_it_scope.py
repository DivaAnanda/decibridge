"""Round 5 item 5: Admin IT handles users, the system and backups, not case content.

Pak Anom: "Admin IT: batasi hanya urusan user/system/backup. Tidak boleh mengubah isi
analisis atau menerbitkan keputusan." The 23092026 Panduan adds the least-privilege
rule: "Admin IT tidak melihat/mengedit detailed clinical/economic case content".
Admin IT keeps the case list as metadata (ID, title, status, dates, integrity) and the
archive seal, and loses every analysis endpoint.
"""

from __future__ import annotations

import pytest
from rest_framework.test import APIClient

from apps.accounts.models import RoleSlug

pytestmark = pytest.mark.django_db

CONTENT_ENDPOINTS = [
    "readiness/",
    "econ/model/",
    "econ/parameters/",
    "econ/results/",
    "econ/results/latest/",
    "econ/bia/results/",
    "econ/bia/results/latest/",
    "econ/psa/results/latest/",
    "econ/validate/template/",
    "cea/input/",
    "cea/results/",
    "cea/results/latest/",
    "bia/input/",
    "bia/results/",
    "bia/results/latest/",
    "references/",
    "etd/appraisals/",
    "etd/summary/",
    "weights/",
    "weights/summary/",
    "cba/",
    "recommendation/results/",
    "recommendation/results/latest/",
    "approvals/",
    "policy-briefs/",
    "versions/",
]

CONTENT_FIELDS = {
    "technology",
    "comparator",
    "indication",
    "population",
    "setting",
    "perspective",
    "decision_questions",
    "versions",
}


def _url(case_id: str, suffix: str = "") -> str:
    return f"/api/v1/cases/{case_id}/{suffix}"


def _client_for(user) -> APIClient:
    client = APIClient()
    client.force_authenticate(user=user)
    return client


@pytest.fixture
def no_role_client(user_factory):
    return _client_for(user_factory(email="norole@example.com"))


@pytest.fixture
def admin_and_analyst_client(user_factory, role_factory):
    user = user_factory(email="both@example.com")
    user.groups.add(role_factory(RoleSlug.ADMIN_IT).group)
    user.groups.add(role_factory(RoleSlug.HTA_ANALYST).group)
    return _client_for(user)


class TestAdminItSeesMetadataOnly:
    def test_case_list_rows_carry_no_clinical_fields(self, admin_it_client, pilot_case):
        response = admin_it_client.get("/api/v1/cases/")

        assert response.status_code == 200
        row = response.data["results"][0]
        assert row["case_id"] == pilot_case.case_id
        assert row["case_title"] == pilot_case.case_title
        assert {"status", "integrity_flag", "created_at", "updated_at"} <= set(row)
        assert not CONTENT_FIELDS & set(row)

    def test_case_detail_carries_no_clinical_fields(self, admin_it_client, pilot_case):
        response = admin_it_client.get(_url(pilot_case.case_id))

        assert response.status_code == 200
        assert response.data["case_id"] == pilot_case.case_id
        assert {"status", "integrity_flag", "integrity_notes", "is_locked"} <= set(response.data)
        assert not CONTENT_FIELDS & set(response.data)
        assert response.data["allowed_transitions"] == []

    @pytest.mark.parametrize("suffix", CONTENT_ENDPOINTS)
    def test_analysis_endpoints_are_refused(self, admin_it_client, pilot_case, suffix):
        response = admin_it_client.get(_url(pilot_case.case_id, suffix))

        assert response.status_code == 403, suffix

    def test_cannot_edit_case_metadata(self, admin_it_client, pilot_case):
        response = admin_it_client.patch(
            _url(pilot_case.case_id), {"case_title": "diubah"}, format="json"
        )

        assert response.status_code == 403

    def test_cannot_run_a_transition(self, admin_it_client, pilot_case):
        response = admin_it_client.post(
            _url(pilot_case.case_id, "transition/"), {"action": "submit"}, format="json"
        )

        assert response.status_code == 403
        pilot_case.refresh_from_db()
        assert pilot_case.status == "draft"


class TestOtherRolesKeepContent:
    def test_kft_member_still_gets_the_full_list_row(self, kft_member_client, pilot_case):
        row = kft_member_client.get("/api/v1/cases/").data["results"][0]

        assert row["technology"] == pilot_case.technology

    def test_kft_member_still_reads_analysis(self, kft_member_client, pilot_case):
        assert kft_member_client.get(_url(pilot_case.case_id, "etd/summary/")).status_code == 200

    def test_a_content_role_beside_admin_it_keeps_content(
        self, admin_and_analyst_client, pilot_case
    ):
        detail = admin_and_analyst_client.get(_url(pilot_case.case_id)).data
        summary = admin_and_analyst_client.get(_url(pilot_case.case_id, "etd/summary/"))

        assert detail["population"] == pilot_case.population
        assert summary.status_code == 200


class TestReadsThatOnlyCheckedLogin:
    """These answered any signed-in account, whatever its role."""

    @pytest.mark.parametrize(
        "suffix",
        [
            "etd/summary/",
            "weights/summary/",
            "recommendation/results/",
            "recommendation/results/latest/",
        ],
    )
    def test_an_account_without_a_role_is_refused(self, no_role_client, pilot_case, suffix):
        assert no_role_client.get(_url(pilot_case.case_id, suffix)).status_code == 403


class TestSearchStaysWithinWhatAdminItSees:
    """Code review: searching by drug name revealed which cases concern it."""

    def test_admin_it_cannot_search_by_intervention(self, admin_it_client, pilot_case):
        response = admin_it_client.get("/api/v1/cases/", {"search": "Sacubitril"})

        assert response.data["count"] == 0

    def test_admin_it_can_search_by_id(self, admin_it_client, pilot_case):
        response = admin_it_client.get("/api/v1/cases/", {"search": pilot_case.case_id})

        assert response.data["count"] == 1

    def test_content_roles_still_search_by_intervention(self, kft_member_client, pilot_case):
        response = kft_member_client.get("/api/v1/cases/", {"search": "Sacubitril"})

        assert response.data["count"] == 1
