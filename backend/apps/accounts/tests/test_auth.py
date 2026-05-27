from __future__ import annotations

import pytest
from rest_framework import status


@pytest.mark.django_db
class TestLogin:
    def test_login_success_returns_tokens_and_user(self, api_client, hta_user):
        response = api_client.post(
            "/api/v1/auth/login/",
            {"email": hta_user.email, "password": "TestPass123!"},
            format="json",
        )
        assert response.status_code == status.HTTP_200_OK
        assert "access" in response.data
        assert "refresh" in response.data
        assert response.data["user"]["email"] == hta_user.email
        assert any(r["slug"] == "hta_analyst" for r in response.data["user"]["roles"])

    def test_login_wrong_password_rejects(self, api_client, hta_user):
        response = api_client.post(
            "/api/v1/auth/login/",
            {"email": hta_user.email, "password": "WrongPassword"},
            format="json",
        )
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_login_unknown_user_rejects(self, api_client):
        response = api_client.post(
            "/api/v1/auth/login/",
            {"email": "nobody@example.com", "password": "whatever"},
            format="json",
        )
        assert response.status_code == status.HTTP_401_UNAUTHORIZED


@pytest.mark.django_db
class TestMe:
    def test_me_returns_authenticated_user(self, authed_client, hta_user):
        response = authed_client.get("/api/v1/auth/me/")
        assert response.status_code == status.HTTP_200_OK
        assert response.data["email"] == hta_user.email
        assert response.data["roles"][0]["slug"] == "hta_analyst"

    def test_me_unauthenticated_rejects(self, api_client):
        response = api_client.get("/api/v1/auth/me/")
        assert response.status_code == status.HTTP_401_UNAUTHORIZED


@pytest.mark.django_db
class TestLogout:
    def test_logout_blacklists_refresh_token(self, api_client, hta_user):
        login = api_client.post(
            "/api/v1/auth/login/",
            {"email": hta_user.email, "password": "TestPass123!"},
            format="json",
        )
        refresh = login.data["refresh"]
        api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {login.data['access']}")
        response = api_client.post("/api/v1/auth/logout/", {"refresh": refresh}, format="json")
        assert response.status_code == status.HTTP_205_RESET_CONTENT

        refresh_again = api_client.post(
            "/api/v1/auth/refresh/", {"refresh": refresh}, format="json"
        )
        assert refresh_again.status_code == status.HTTP_401_UNAUTHORIZED
