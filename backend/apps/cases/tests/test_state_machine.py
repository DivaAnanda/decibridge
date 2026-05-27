from __future__ import annotations

import pytest
from django.core.exceptions import PermissionDenied, ValidationError

from apps.cases.models import CaseStatus
from apps.cases.state_machine import TRANSITIONS, allowed_transitions_for, transition


@pytest.mark.django_db
class TestSubmit:
    def test_hta_can_submit_draft(self, pilot_case, hta_user):
        assert pilot_case.status == CaseStatus.DRAFT
        transition(pilot_case, "submit", hta_user)
        assert pilot_case.status == CaseStatus.IN_REVIEW

    def test_sekretaris_can_submit_draft(self, pilot_case, sekretaris_user):
        transition(pilot_case, "submit", sekretaris_user)
        assert pilot_case.status == CaseStatus.IN_REVIEW

    def test_kft_member_cannot_submit(self, pilot_case, kft_member_user):
        with pytest.raises(PermissionDenied):
            transition(pilot_case, "submit", kft_member_user)

    def test_cannot_submit_from_approved(self, pilot_case, hta_user, ketua_user):
        transition(pilot_case, "submit", hta_user)
        transition(pilot_case, "approve", ketua_user)
        with pytest.raises(ValidationError):
            transition(pilot_case, "submit", hta_user)


@pytest.mark.django_db
class TestApprove:
    def test_ketua_can_approve_in_review(self, pilot_case, hta_user, ketua_user):
        transition(pilot_case, "submit", hta_user)
        transition(pilot_case, "approve", ketua_user)
        assert pilot_case.status == CaseStatus.APPROVED

    def test_hta_cannot_approve(self, pilot_case, hta_user):
        transition(pilot_case, "submit", hta_user)
        with pytest.raises(PermissionDenied):
            transition(pilot_case, "approve", hta_user)


@pytest.mark.django_db
class TestSendBackRequiresReason:
    def test_send_back_without_reason_rejected(self, pilot_case, hta_user, ketua_user):
        transition(pilot_case, "submit", hta_user)
        with pytest.raises(ValidationError):
            transition(pilot_case, "send_back", ketua_user, reason="")

    def test_send_back_with_reason_accepted(self, pilot_case, hta_user, ketua_user):
        transition(pilot_case, "submit", hta_user)
        transition(pilot_case, "send_back", ketua_user, reason="Missing references")
        assert pilot_case.status == CaseStatus.DRAFT


@pytest.mark.django_db
class TestLockAndArchive:
    def test_full_lifecycle(self, pilot_case, hta_user, ketua_user, admin_it_user):
        transition(pilot_case, "submit", hta_user)
        transition(pilot_case, "approve", ketua_user)
        transition(pilot_case, "lock", ketua_user)
        assert pilot_case.status == CaseStatus.LOCKED
        assert pilot_case.is_locked is True
        transition(pilot_case, "archive", admin_it_user)
        assert pilot_case.status == CaseStatus.ARCHIVED


@pytest.mark.django_db
class TestAllowedTransitions:
    def test_draft_hta_sees_submit_only(self, pilot_case, hta_user):
        names = {t.name for t in allowed_transitions_for(pilot_case, hta_user)}
        assert names == {"submit"}

    def test_in_review_ketua_sees_approve_and_send_back(self, pilot_case, hta_user, ketua_user):
        transition(pilot_case, "submit", hta_user)
        names = {t.name for t in allowed_transitions_for(pilot_case, ketua_user)}
        assert names == {"approve", "send_back"}

    def test_locked_admin_sees_archive(self, pilot_case, hta_user, ketua_user, admin_it_user):
        transition(pilot_case, "submit", hta_user)
        transition(pilot_case, "approve", ketua_user)
        transition(pilot_case, "lock", ketua_user)
        names = {t.name for t in allowed_transitions_for(pilot_case, admin_it_user)}
        assert "archive" in names

    def test_unknown_transition_raises(self, pilot_case, hta_user):
        with pytest.raises(KeyError):
            transition(pilot_case, "nuke_from_orbit", hta_user)


@pytest.mark.django_db
class TestTransitionCatalogue:
    def test_every_transition_has_unique_name(self):
        names = [t.name for t in TRANSITIONS.values()]
        assert len(names) == len(set(names))
