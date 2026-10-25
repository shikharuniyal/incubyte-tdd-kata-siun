"""POST /api/auth/register, POST /api/auth/login and the token lifecycle."""

import pytest

from dealership.models import AppUser, Customer, Party, Person

pytestmark = pytest.mark.django_db

REGISTER_URL = "/api/auth/register"
LOGIN_URL = "/api/auth/login"
REFRESH_URL = "/api/auth/refresh"
LOGOUT_URL = "/api/auth/logout"
ME_URL = "/api/auth/me"

VALID_REGISTRATION = {
    "first_name": "Asha",
    "last_name": "Kumar",
    "email": "asha@example.com",
    "password": "Str0ng-Passw0rd!",
}


def register(api_client, **overrides):
    return api_client.post(REGISTER_URL, {**VALID_REGISTRATION, **overrides}, format="json")


def login(api_client, email="asha@example.com", password="Str0ng-Passw0rd!"):
    return api_client.post(LOGIN_URL, {"email": email, "password": password}, format="json")


class TestRegister:
    def test_creates_an_account_and_returns_tokens(self, api_client):
        response = register(api_client)

        assert response.status_code == 201
        body = response.json()
        assert body["access"] and body["refresh"]
        assert body["user"]["email"] == "asha@example.com"
        assert body["user"]["name"] == "Asha Kumar"
        assert body["user"]["is_admin"] is False

    def test_records_the_person_as_a_customer_party(self, api_client):
        register(api_client)

        user = AppUser.objects.get(email="asha@example.com")
        assert user.person.given_name == "Asha"
        assert user.person.family_name == "Kumar"
        assert user.person.party.party_type == Party.Type.PERSON
        assert user.person.party.display_name == "Asha Kumar"
        assert Customer.objects.filter(party=user.person.party).exists()

    def test_stores_a_password_hash_not_the_password(self, api_client):
        register(api_client)

        user = AppUser.objects.get(email="asha@example.com")
        assert user.password != VALID_REGISTRATION["password"]
        assert user.check_password(VALID_REGISTRATION["password"])

    def test_normalises_the_email_to_lower_case(self, api_client):
        register(api_client, email="  Asha@Example.COM ")

        assert AppUser.objects.filter(email="asha@example.com").exists()

    def test_rejects_a_duplicate_email_case_insensitively(self, api_client):
        register(api_client)

        response = register(api_client, email="ASHA@example.com")

        assert response.status_code == 400
        assert "email" in response.json()
        assert AppUser.objects.count() == 1

    def test_rejects_a_weak_password(self, api_client):
        response = register(api_client, password="12345")

        assert response.status_code == 400
        assert "password" in response.json()
        assert not Person.objects.exists()

    @pytest.mark.parametrize("missing", ["first_name", "last_name", "email", "password"])
    def test_requires_every_field(self, api_client, missing):
        payload = {k: v for k, v in VALID_REGISTRATION.items() if k != missing}

        response = api_client.post(REGISTER_URL, payload, format="json")

        assert response.status_code == 400
        assert missing in response.json()

    def test_rejects_an_invalid_email(self, api_client):
        response = register(api_client, email="not-an-email")

        assert response.status_code == 400
        assert "email" in response.json()


class TestLogin:
    def test_returns_tokens_for_valid_credentials(self, api_client):
        register(api_client)

        response = login(api_client)

        assert response.status_code == 200
        body = response.json()
        assert body["access"] and body["refresh"]
        assert body["user"]["email"] == "asha@example.com"

    def test_email_is_case_insensitive(self, api_client):
        register(api_client)

        assert login(api_client, email="ASHA@EXAMPLE.COM").status_code == 200

    def test_rejects_a_wrong_password(self, api_client):
        register(api_client)

        response = login(api_client, password="wrong-password")

        assert response.status_code == 401
        assert response.json()["detail"] == "Invalid email or password."

    def test_rejects_an_unknown_email_with_the_same_message(self, api_client):
        response = login(api_client, email="nobody@example.com")

        assert response.status_code == 401
        assert response.json()["detail"] == "Invalid email or password."

    def test_rejects_a_deactivated_account(self, api_client):
        register(api_client)
        AppUser.objects.filter(email="asha@example.com").update(is_active=False)

        assert login(api_client).status_code == 401


class TestAccessToken:
    def test_me_returns_the_authenticated_user(self, api_client):
        access = register(api_client).json()["access"]
        api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {access}")

        response = api_client.get(ME_URL)

        assert response.status_code == 200
        assert response.json()["email"] == "asha@example.com"

    def test_protected_endpoints_require_a_token(self, api_client):
        response = api_client.get(ME_URL)

        assert response.status_code == 401

    def test_rejects_a_tampered_token(self, api_client):
        access = register(api_client).json()["access"]
        api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {access[:-2]}xx")

        assert api_client.get(ME_URL).status_code == 401

    def test_rejects_a_malformed_authorization_header(self, api_client):
        api_client.credentials(HTTP_AUTHORIZATION="Token abc")

        assert api_client.get(ME_URL).status_code == 401

    def test_rejects_an_expired_token(self, api_client, settings):
        settings.JWT_SETTINGS = {**settings.JWT_SETTINGS, "ACCESS_TOKEN_LIFETIME": -settings.JWT_SETTINGS["ACCESS_TOKEN_LIFETIME"]}
        access = register(api_client).json()["access"]
        api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {access}")

        assert api_client.get(ME_URL).status_code == 401

    def test_a_refresh_token_cannot_be_used_as_an_access_token(self, api_client):
        refresh = register(api_client).json()["refresh"]
        api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {refresh}")

        assert api_client.get(ME_URL).status_code == 401

    def test_rejects_the_token_of_a_deactivated_user(self, api_client):
        access = register(api_client).json()["access"]
        AppUser.objects.filter(email="asha@example.com").update(is_active=False)
        api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {access}")

        assert api_client.get(ME_URL).status_code == 401


class TestRefreshAndLogout:
    def test_refresh_issues_a_new_token_pair(self, api_client):
        refresh = register(api_client).json()["refresh"]

        response = api_client.post(REFRESH_URL, {"refresh": refresh}, format="json")

        assert response.status_code == 200
        body = response.json()
        assert body["access"]
        assert body["refresh"] and body["refresh"] != refresh

    def test_a_refresh_token_can_only_be_used_once(self, api_client):
        refresh = register(api_client).json()["refresh"]
        api_client.post(REFRESH_URL, {"refresh": refresh}, format="json")

        response = api_client.post(REFRESH_URL, {"refresh": refresh}, format="json")

        assert response.status_code == 401

    def test_rejects_an_unknown_refresh_token(self, api_client):
        response = api_client.post(REFRESH_URL, {"refresh": "made-up"}, format="json")

        assert response.status_code == 401

    def test_logout_revokes_the_refresh_token(self, api_client):
        refresh = register(api_client).json()["refresh"]

        logout = api_client.post(LOGOUT_URL, {"refresh": refresh}, format="json")
        reuse = api_client.post(REFRESH_URL, {"refresh": refresh}, format="json")

        assert logout.status_code == 204
        assert reuse.status_code == 401
