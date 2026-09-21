"""Round 4 item 4: every stage refuses a direct API call when incomplete.

    "Uji bahwa backend menolak tindakan ketika persyaratan belum terpenuhi,
     meskipun permintaan dikirim langsung. Pesan penolakan harus menyebutkan
     komponen yang kurang."

A disabled button proves nothing about the backend, so each of these posts to the
endpoint as the *authorised* role and asserts the refusal plus the named gaps.
Role rejection is covered elsewhere; here every caller is allowed to act and is
stopped purely by the dossier being incomplete.

Requirements per stage are documented in `docs/stage-requirements.md`.
"""

from __future__ import annotations

from decimal import Decimal

import pytest
from django.urls import reverse

from apps.cases.models import Case, CaseStatus, DecisionQuestion

pytestmark = pytest.mark.django_db

PASSWORD = "TestPass123!"


def _transition_url(case_id: str) -> str:
    return f"/api/v1/cases/{case_id}/transition/"


def _add_pico(case) -> None:
    DecisionQuestion.objects.create(
        case=case,
        order=1,
        question_text="Apakah ARNI perlu masuk formularium?",
        pico_population="Pasien HFrEF dewasa",
        pico_intervention="ARNI",
        pico_comparator="ACEI",
        pico_outcome="Rehospitalisasi 12 bulan",
    )


def _force_status(case, status: str) -> None:
    Case.objects.filter(pk=case.pk).update(status=status)
    case.refresh_from_db()


class TestSubmitStage:
    def test_submit_is_refused_without_pico(self, hta_client, pilot_case):
        response = hta_client.post(
            _transition_url(pilot_case.case_id), {"action": "submit"}, format="json"
        )

        assert response.status_code == 422
        assert "Pertanyaan keputusan (PICO) lengkap" in response.data["missing"]

    def test_submit_does_not_demand_the_analysis_it_exists_to_review(
        self, hta_client, pilot_case
    ):
        """Submitting for review is what produces CEA/BIA/EtD, so requiring them
        here would make the stage impossible to reach."""
        _add_pico(pilot_case)

        response = hta_client.post(
            _transition_url(pilot_case.case_id), {"action": "submit"}, format="json"
        )

        assert response.status_code == 200, response.data
        pilot_case.refresh_from_db()
        assert pilot_case.status == CaseStatus.IN_REVIEW


class TestRecommendationStage:
    def test_compute_names_every_missing_component(self, hta_client, pilot_case):
        url = reverse("recommendation:compute", args=[pilot_case.case_id])

        response = hta_client.post(url, {}, format="json")

        assert response.status_code == 422
        body = str(response.data)
        assert "EtD" in body
        assert "ekonomi" in body.lower()

    def test_empty_components_are_never_scored_as_zero_or_favourable(
        self, hta_client, pilot_case
    ):
        """'Data kosong tidak boleh otomatis dianggap nol atau mendapat skor
        menguntungkan.'"""
        url = reverse("recommendation:compute", args=[pilot_case.case_id])

        response = hta_client.post(url, {}, format="json")

        body = str(response.data).lower()
        assert "hijau" not in body
        assert "green" not in body


class TestApprovalStage:
    def test_approve_transition_is_refused_when_incomplete(
        self, ketua_client, pilot_case, hta_user
    ):
        _add_pico(pilot_case)
        _force_status(pilot_case, CaseStatus.IN_REVIEW)

        response = ketua_client.post(
            _transition_url(pilot_case.case_id), {"action": "approve"}, format="json"
        )

        assert response.status_code == 422
        assert "Analisis ekonomi deterministik (CEA)" in response.data["missing"]

    def test_signoff_endpoint_is_refused_when_incomplete(
        self, ketua_client, pilot_case, hta_user
    ):
        from apps.recommendation.models import Recommendation

        _add_pico(pilot_case)
        _force_status(pilot_case, CaseStatus.IN_REVIEW)
        rec = Recommendation.objects.create(
            case=pilot_case,
            input_snapshot={},
            composite_score=Decimal("85.00"),
            traffic_light="green",
            justification_text="seed",
            algorithm_version="2.0.0",
            computed_by=hta_user,
        )

        response = ketua_client.post(
            reverse("approval:sign", args=[pilot_case.case_id]),
            {
                "recommendation_id": rec.pk,
                "decision": "approved",
                "confirmation_acknowledged": True,
                "password": PASSWORD,
            },
            format="json",
        )

        assert response.status_code == 422
        assert response.data["missing"]


class TestLockStage:
    def test_lock_is_refused_without_a_recorded_signature(
        self, ketua_client, pilot_case
    ):
        _add_pico(pilot_case)
        _force_status(pilot_case, CaseStatus.APPROVED)

        response = ketua_client.post(
            _transition_url(pilot_case.case_id), {"action": "lock"}, format="json"
        )

        assert response.status_code == 422
        assert "Sign-off Ketua KFT tercatat" in response.data["missing"]


class TestBriefStage:
    def test_brief_generation_is_refused_when_incomplete(
        self, hta_client, pilot_case, hta_user
    ):
        from apps.recommendation.models import Recommendation

        Recommendation.objects.create(
            case=pilot_case,
            input_snapshot={},
            composite_score=Decimal("85.00"),
            traffic_light="green",
            justification_text="legacy",
            algorithm_version="1.0.0",
            computed_by=hta_user,
        )
        _force_status(pilot_case, CaseStatus.LOCKED)

        response = hta_client.post(f"/api/v1/cases/{pilot_case.case_id}/policy-briefs/")

        assert response.status_code == 422
        assert response.data["missing"]


class TestArchiveStage:
    def test_archive_is_refused_when_integrity_fails(self, ketua_client, pilot_case):
        _force_status(pilot_case, CaseStatus.LOCKED)

        response = ketua_client.post(
            _transition_url(pilot_case.case_id),
            {"action": "archive", "reason": "retensi"},
            format="json",
        )

        assert response.status_code == 422
        assert response.data["missing"]

    def test_refusal_names_the_missing_snapshot(self, ketua_client, pilot_case):
        _force_status(pilot_case, CaseStatus.LOCKED)

        response = ketua_client.post(
            _transition_url(pilot_case.case_id),
            {"action": "archive", "reason": "retensi"},
            format="json",
        )

        assert "Snapshot keputusan tersimpan dan tidak dapat diubah" in response.data["missing"]
