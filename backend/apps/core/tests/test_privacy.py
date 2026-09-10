"""Round 3: audit IPs are visible in full only to Admin IT."""

from __future__ import annotations

import pytest

from apps.core.privacy import mask_ip, may_see_full_ip

pytestmark = pytest.mark.django_db


class TestMaskIP:
    def test_ipv4_keeps_the_network_and_hides_the_host(self):
        assert mask_ip("203.0.113.42") == "203.0.113.xxx"

    def test_two_hosts_on_one_subnet_are_indistinguishable(self):
        assert mask_ip("203.0.113.42") == mask_ip("203.0.113.99")

    def test_two_different_subnets_stay_distinguishable(self):
        assert mask_ip("203.0.113.42") != mask_ip("198.51.100.42")

    def test_ipv6_is_masked(self):
        masked = mask_ip("2001:db8:85a3:0:0:8a2e:370:7334")
        assert masked.endswith("xxxx")
        assert masked.startswith("2001:db8")

    def test_none_and_empty_pass_through(self):
        assert mask_ip(None) is None
        assert mask_ip("") == ""


class TestMaySeeFullIP:
    def test_admin_it_may(self, admin_it_user):
        assert may_see_full_ip(admin_it_user) is True

    def test_sekretaris_may_not(self, sekretaris_user):
        assert may_see_full_ip(sekretaris_user) is False

    def test_ketua_may_not(self, ketua_user):
        assert may_see_full_ip(ketua_user) is False

    def test_anonymous_may_not(self):
        assert may_see_full_ip(None) is False


class TestAuditSurfacesMaskByDefault:
    """The serializer context is what actually decides this, so exercise the API."""

    def _sign(self, case, user, ip: str = "203.0.113.42"):
        from decimal import Decimal

        from django.utils import timezone

        from apps.approval.models import Approval, ApprovalDecision
        from apps.recommendation.models import Recommendation

        rec = Recommendation.objects.create(
            case=case,
            input_snapshot={},
            composite_score=Decimal("85.00"),
            traffic_light="green",
            justification_text="seed",
            algorithm_version="2.0.0",
            computed_by=user,
        )
        return Approval.objects.create(
            case=case,
            recommendation=rec,
            approver=user,
            decision=ApprovalDecision.APPROVED,
            confirmation_acknowledged=True,
            password_verified_at=timezone.now(),
            reason="ok",
            ip_address=ip,
        )

    def test_sekretaris_sees_a_masked_approval_ip(
        self, sekretaris_client, pilot_case, ketua_user
    ):
        self._sign(pilot_case, ketua_user)

        response = sekretaris_client.get(f"/api/v1/cases/{pilot_case.case_id}/approvals/")

        assert response.status_code == 200
        assert response.data[0]["ip_address"] == "203.0.113.xxx"

    def test_admin_it_sees_the_full_approval_ip(
        self, admin_it_client, pilot_case, ketua_user
    ):
        self._sign(pilot_case, ketua_user)

        response = admin_it_client.get(f"/api/v1/cases/{pilot_case.case_id}/approvals/")

        assert response.status_code == 200
        assert response.data[0]["ip_address"] == "203.0.113.42"
