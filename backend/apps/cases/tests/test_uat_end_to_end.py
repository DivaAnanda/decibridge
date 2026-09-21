"""Round 4 item 5: the whole workflow driven through the API by all five roles.

    "Jalankan kasus UAT dari pembuatan kasus, pengisian analisis, penilaian KFT,
     pengajuan tinjauan, rekomendasi, sign-off Ketua, penguncian, hingga brief
     dan arsip sesuai alur yang disepakati. Sertakan pengujian permintaan revisi
     dan penolakan. Pastikan setiap tindakan hanya dapat dilakukan role
     berwenang dan tercatat dalam audit trail. Pemeriksaan tampilan saja belum
     cukup untuk membuktikan pembatasan backend."

Everything here goes through HTTP with a real authenticated client per role. No
model-layer shortcuts for any action a person would take, so a passing run is
evidence about the backend rather than about the screen.
"""

from __future__ import annotations

from decimal import Decimal

import pytest

from apps.audit.models import AuditLog
from apps.cases.models import Case, CaseStatus

pytestmark = pytest.mark.django_db

PASSWORD = "TestPass123!"
CASE_ID = "UAT_E2E_001"

CASE_PAYLOAD = {
    "case_id": CASE_ID,
    "case_title": "UAT - bukan keputusan klinis - alur penuh",
    "technology": "ARNI (sacubitril/valsartan)",
    "comparator": "ACEI (captopril)",
    "indication": "HFrEF",
    "perspective": "hospital",
    "decision_question": {
        "question_text": "Apakah ARNI perlu masuk formularium untuk HFrEF?",
        "pico_population": "Pasien HFrEF dewasa, EF <= 40%",
        "pico_intervention": "ARNI",
        "pico_comparator": "ACEI",
        "pico_outcome": "Rehospitalisasi 12 bulan",
    },
}


def _transition(client, action: str, reason: str = ""):
    payload = {"action": action}
    if reason:
        payload["reason"] = reason
    return client.post(f"/api/v1/cases/{CASE_ID}/transition/", payload, format="json")


@pytest.fixture
def analysed_case(hta_client, hta_user, kft_member_client, kft_member_user):
    """Case created and analysed through the API up to the point of submission."""
    from apps.econ.models import EconomicModel
    from apps.econ.validation_fixtures import MODEL_SCALARS, VALIDATION_PARAMETERS

    assert hta_client.post("/api/v1/cases/", CASE_PAYLOAD, format="json").status_code == 201
    case = Case.objects.get(case_id=CASE_ID)

    # Economic model + parameters, then the engines, all over HTTP.
    assert hta_client.put(
        f"/api/v1/cases/{CASE_ID}/econ/model/",
        {k: str(v) for k, v in MODEL_SCALARS.items()},
        format="json",
    ).status_code in {200, 201}

    params = [
        {
            "key": spec["key"],
            "alternative": spec["alternative"],
            "value": str(spec["value"]),
            "param_type": spec["param_type"],
            "data_status": spec.get("data_status", "observed"),
            "unit": spec.get("unit", ""),
            "source_reference": spec.get("source_reference", "UAT sintetis"),
        }
        for spec in VALIDATION_PARAMETERS
    ]
    assert hta_client.put(
        f"/api/v1/cases/{CASE_ID}/econ/parameters/", params, format="json"
    ).status_code in {200, 201}

    assert hta_client.post(f"/api/v1/cases/{CASE_ID}/econ/compute/").status_code in {200, 201}
    assert hta_client.post(f"/api/v1/cases/{CASE_ID}/econ/bia/compute/").status_code in {200, 201}

    # KFT member appraises all nine domains.
    domains = kft_member_client.get("/api/v1/etd/domains/").data
    reference = hta_client.post(
        f"/api/v1/cases/{CASE_ID}/references/",
        {"citation_text": "Rujukan sintetis UAT.", "reference_type": "journal_article"},
        format="json",
    ).data
    for domain in domains:
        response = kft_member_client.post(
            f"/api/v1/cases/{CASE_ID}/etd/appraisals/",
            {
                "domain_slug": domain["slug"],
                "judgement": 75,
                "certainty": "high",
                "narrative": "Penilaian sintetis UAT.",
                "reference_ids": [reference["id"]],
            },
            format="json",
        )
        assert response.status_code in {200, 201}, response.data

    assert hta_client.post(
        f"/api/v1/cases/{CASE_ID}/recommendation/compute/", {}, format="json"
    ).status_code in {200, 201}

    case.refresh_from_db()
    return case


class TestRoleSeparationAcrossTheWalk:
    """Each step attempted by a role that must not perform it."""

    def test_kft_member_cannot_create_a_case(self, kft_member_client):
        response = kft_member_client.post("/api/v1/cases/", CASE_PAYLOAD, format="json")

        assert response.status_code == 403

    def test_kft_member_cannot_run_the_economics(self, kft_member_client, analysed_case):
        response = kft_member_client.post(f"/api/v1/cases/{CASE_ID}/econ/compute/")

        assert response.status_code == 403

    def test_hta_cannot_appraise_etd(self, hta_client, analysed_case):
        response = hta_client.post(
            f"/api/v1/cases/{CASE_ID}/etd/appraisals/",
            {"domain_slug": "problem", "judgement": 75, "certainty": "high"},
            format="json",
        )

        assert response.status_code == 403

    def test_hta_cannot_approve(self, hta_client, analysed_case):
        _transition(hta_client, "submit")

        response = _transition(hta_client, "approve")

        assert response.status_code == 403

    def test_admin_it_cannot_sign_off(self, admin_it_client, analysed_case, hta_client):
        _transition(hta_client, "submit")
        rec_id = hta_client.get(
            f"/api/v1/cases/{CASE_ID}/recommendation/results/latest/"
        ).data["id"]

        response = admin_it_client.post(
            f"/api/v1/cases/{CASE_ID}/approvals/sign/",
            {
                "recommendation_id": rec_id,
                "decision": "approved",
                "confirmation_acknowledged": True,
                "password": PASSWORD,
            },
            format="json",
        )

        assert response.status_code == 403


class TestRevisionAndRejection:
    """'Sertakan pengujian permintaan revisi dan penolakan.'"""

    def test_ketua_can_send_a_case_back_for_revision(
        self, hta_client, ketua_client, analysed_case
    ):
        _transition(hta_client, "submit")

        response = _transition(ketua_client, "send_back", reason="Perlu data biaya terbaru")

        assert response.status_code == 200, response.data
        analysed_case.refresh_from_db()
        assert analysed_case.status == CaseStatus.DRAFT

    def test_send_back_requires_a_reason(self, hta_client, ketua_client, analysed_case):
        _transition(hta_client, "submit")

        response = _transition(ketua_client, "send_back")

        assert response.status_code == 400

    def test_a_returned_case_can_be_resubmitted(
        self, hta_client, ketua_client, analysed_case
    ):
        _transition(hta_client, "submit")
        _transition(ketua_client, "send_back", reason="Perlu revisi")

        response = _transition(hta_client, "submit")

        assert response.status_code == 200, response.data
        analysed_case.refresh_from_db()
        assert analysed_case.status == CaseStatus.IN_REVIEW

    def test_ketua_can_reject_at_sign_off(self, hta_client, ketua_client, analysed_case):
        _transition(hta_client, "submit")
        rec_id = hta_client.get(
            f"/api/v1/cases/{CASE_ID}/recommendation/results/latest/"
        ).data["id"]

        response = ketua_client.post(
            f"/api/v1/cases/{CASE_ID}/approvals/sign/",
            {
                "recommendation_id": rec_id,
                "decision": "rejected",
                "confirmation_acknowledged": True,
                "password": PASSWORD,
                "reason": "Rasio biaya-manfaat belum memadai",
            },
            format="json",
        )

        assert response.status_code == 201, response.data
        analysed_case.refresh_from_db()
        assert analysed_case.status != CaseStatus.LOCKED


class TestHappyPathThroughToArchive:
    def test_full_lifecycle(self, hta_client, ketua_client, analysed_case):
        _transition(hta_client, "submit")

        rec_id = hta_client.get(
            f"/api/v1/cases/{CASE_ID}/recommendation/results/latest/"
        ).data["id"]
        sign = ketua_client.post(
            f"/api/v1/cases/{CASE_ID}/approvals/sign/",
            {
                "recommendation_id": rec_id,
                "decision": "approved",
                "confirmation_acknowledged": True,
                "password": PASSWORD,
            },
            format="json",
        )
        assert sign.status_code == 201, sign.data

        analysed_case.refresh_from_db()
        assert analysed_case.status == CaseStatus.APPROVED

        lock = _transition(ketua_client, "lock")
        assert lock.status_code == 200, lock.data
        analysed_case.refresh_from_db()
        assert analysed_case.status == CaseStatus.LOCKED

        brief = ketua_client.post(f"/api/v1/cases/{CASE_ID}/policy-briefs/")
        assert brief.status_code == 201, brief.data

        archive = _transition(ketua_client, "archive", reason="Selesai diuji")
        assert archive.status_code == 200, archive.data
        analysed_case.refresh_from_db()
        assert analysed_case.status == CaseStatus.ARCHIVED

    def test_every_transition_is_recorded_in_the_audit_trail(
        self, hta_client, ketua_client, analysed_case
    ):
        _transition(hta_client, "submit")
        _transition(ketua_client, "send_back", reason="Perlu revisi")
        _transition(hta_client, "submit")

        transitions = [
            entry.metadata.get("transition")
            for entry in AuditLog.objects.all()
            if entry.metadata
        ]

        assert "submit" in transitions
        assert "send_back" in transitions

    def test_locked_case_rejects_further_edits(self, hta_client, ketua_client, analysed_case):
        _transition(hta_client, "submit")
        rec_id = hta_client.get(
            f"/api/v1/cases/{CASE_ID}/recommendation/results/latest/"
        ).data["id"]
        ketua_client.post(
            f"/api/v1/cases/{CASE_ID}/approvals/sign/",
            {
                "recommendation_id": rec_id,
                "decision": "approved",
                "confirmation_acknowledged": True,
                "password": PASSWORD,
            },
            format="json",
        )
        _transition(ketua_client, "lock")

        response = hta_client.patch(
            f"/api/v1/cases/{CASE_ID}/",
            {"case_title": "Diubah setelah dikunci"},
            format="json",
        )

        assert response.status_code in {400, 403}
        analysed_case.refresh_from_db()
        assert analysed_case.case_title != "Diubah setelah dikunci"


class TestNoFavourableScoreFromEmptyData:
    def test_recommendation_on_a_bare_case_names_gaps_instead_of_scoring(
        self, hta_client
    ):
        hta_client.post(
            "/api/v1/cases/",
            {**CASE_PAYLOAD, "case_id": "UAT_E2E_KOSONG"},
            format="json",
        )

        response = hta_client.post(
            "/api/v1/cases/UAT_E2E_KOSONG/recommendation/compute/", {}, format="json"
        )

        assert response.status_code == 422
        assert "green" not in str(response.data).lower()


def test_decimal_precision_is_preserved_end_to_end(hta_client, analysed_case):
    """Values must survive the round trip without being rounded in transit."""
    latest = hta_client.get(f"/api/v1/cases/{CASE_ID}/econ/results/latest/").data

    assert Decimal(latest["total_cost_intervention"]) > 0
    assert "." in latest["total_cost_intervention"]
