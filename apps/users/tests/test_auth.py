"""
Tests for user registration and authentication flow.
"""
from __future__ import annotations

import pytest
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

# ─────────────────────────────────────────────────────────────────────────────
# Fixtures
# ─────────────────────────────────────────────────────────────────────────────


@pytest.fixture()
def api_client() -> APIClient:
    return APIClient()


@pytest.fixture()
def register_url() -> str:
    return reverse("users:register")


@pytest.fixture()
def login_url() -> str:
    return reverse("users:login")


@pytest.fixture()
def profile_url() -> str:
    return reverse("users:profile")


@pytest.fixture()
def valid_registration_payload() -> dict:
    return {
        "email": "alice@example.com",
        "first_name": "Alice",
        "last_name": "Smith",
        "phone": "+1-555-0100",
        "password": "StrongP@ss123",
        "password_confirm": "StrongP@ss123",
    }


# ─────────────────────────────────────────────────────────────────────────────
# Registration
# ─────────────────────────────────────────────────────────────────────────────


@pytest.mark.django_db
class TestUserRegistration:
    def test_successful_registration_returns_201(
        self, api_client: APIClient, register_url: str, valid_registration_payload: dict
    ) -> None:
        response = api_client.post(register_url, valid_registration_payload, format="json")

        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        assert data["email"] == valid_registration_payload["email"]
        assert "password" not in data

    def test_duplicate_email_returns_400(
        self, api_client: APIClient, register_url: str, valid_registration_payload: dict
    ) -> None:
        api_client.post(register_url, valid_registration_payload, format="json")
        response = api_client.post(register_url, valid_registration_payload, format="json")

        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_password_mismatch_returns_400(
        self, api_client: APIClient, register_url: str, valid_registration_payload: dict
    ) -> None:
        payload = {**valid_registration_payload, "password_confirm": "WrongPassword"}
        response = api_client.post(register_url, payload, format="json")

        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_missing_email_returns_400(
        self, api_client: APIClient, register_url: str, valid_registration_payload: dict
    ) -> None:
        payload = {k: v for k, v in valid_registration_payload.items() if k != "email"}
        response = api_client.post(register_url, payload, format="json")

        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_weak_password_returns_400(
        self, api_client: APIClient, register_url: str, valid_registration_payload: dict
    ) -> None:
        payload = {**valid_registration_payload, "password": "123", "password_confirm": "123"}
        response = api_client.post(register_url, payload, format="json")

        assert response.status_code == status.HTTP_400_BAD_REQUEST


# ─────────────────────────────────────────────────────────────────────────────
# Login / JWT
# ─────────────────────────────────────────────────────────────────────────────


@pytest.mark.django_db
class TestJWTLogin:
    def test_login_with_valid_credentials_returns_tokens(
        self,
        api_client: APIClient,
        register_url: str,
        login_url: str,
        valid_registration_payload: dict,
    ) -> None:
        # Register first.
        api_client.post(register_url, valid_registration_payload, format="json")

        response = api_client.post(
            login_url,
            {
                "email": valid_registration_payload["email"],
                "password": valid_registration_payload["password"],
            },
            format="json",
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "access" in data
        assert "refresh" in data
        assert "user" in data
        assert data["user"]["email"] == valid_registration_payload["email"]

    def test_login_with_wrong_password_returns_401(
        self,
        api_client: APIClient,
        register_url: str,
        login_url: str,
        valid_registration_payload: dict,
    ) -> None:
        api_client.post(register_url, valid_registration_payload, format="json")

        response = api_client.post(
            login_url,
            {"email": valid_registration_payload["email"], "password": "WrongPassword"},
            format="json",
        )

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_login_with_unknown_email_returns_401(
        self, api_client: APIClient, login_url: str
    ) -> None:
        response = api_client.post(
            login_url,
            {"email": "nobody@example.com", "password": "SomePass"},
            format="json",
        )

        assert response.status_code == status.HTTP_401_UNAUTHORIZED


# ─────────────────────────────────────────────────────────────────────────────
# Profile
# ─────────────────────────────────────────────────────────────────────────────


@pytest.mark.django_db
class TestUserProfile:
    def test_unauthenticated_request_returns_401(
        self, api_client: APIClient, profile_url: str
    ) -> None:
        response = api_client.get(profile_url)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_authenticated_user_can_retrieve_profile(
        self,
        api_client: APIClient,
        register_url: str,
        login_url: str,
        profile_url: str,
        valid_registration_payload: dict,
    ) -> None:
        api_client.post(register_url, valid_registration_payload, format="json")
        login_resp = api_client.post(
            login_url,
            {
                "email": valid_registration_payload["email"],
                "password": valid_registration_payload["password"],
            },
            format="json",
        )
        token = login_resp.json()["access"]
        api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")

        response = api_client.get(profile_url)

        assert response.status_code == status.HTTP_200_OK
        assert response.json()["email"] == valid_registration_payload["email"]

    def test_authenticated_user_can_update_profile(
        self,
        api_client: APIClient,
        register_url: str,
        login_url: str,
        profile_url: str,
        valid_registration_payload: dict,
    ) -> None:
        api_client.post(register_url, valid_registration_payload, format="json")
        login_resp = api_client.post(
            login_url,
            {
                "email": valid_registration_payload["email"],
                "password": valid_registration_payload["password"],
            },
            format="json",
        )
        token = login_resp.json()["access"]
        api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")

        response = api_client.patch(profile_url, {"phone": "+44-7700-900123"}, format="json")

        assert response.status_code == status.HTTP_200_OK
        assert response.json()["phone"] == "+44-7700-900123"
