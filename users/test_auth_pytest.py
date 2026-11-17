import pytest
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient

PASSWORD = "CinemaHub#2026"


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def user(db):
    return get_user_model().objects.create_user(
        username="cinema_user",
        email="user@example.com",
        password=PASSWORD,
    )


@pytest.fixture
def register_payload():
    return {
        "username": "new_user",
        "email": "new@example.com",
        "password": PASSWORD,
        "password_confirmation": PASSWORD,
    }


@pytest.fixture
def access_token(api_client, user):
    response = api_client.post(
        "/api/auth/login/",
        {"username": user.username, "password": PASSWORD},
        format="json",
    )
    return response.data["access"]


@pytest.mark.django_db
def test_register_success(api_client, register_payload):
    response = api_client.post("/api/auth/register/", register_payload, format="json")

    assert response.status_code == 201
    assert response.data["user"]["username"] == register_payload["username"]
    assert "access" in response.data
    assert "refresh" in response.data


@pytest.mark.django_db
def test_register_rejects_missing_invalid_and_mismatched_data(
    api_client, register_payload
):
    assert api_client.post("/api/auth/register/", {}, format="json").status_code == 400

    invalid_email = {**register_payload, "email": "not-an-email"}
    assert (
        api_client.post("/api/auth/register/", invalid_email, format="json").status_code
        == 400
    )

    mismatch = {**register_payload, "password_confirmation": "Different#2026"}
    assert (
        api_client.post("/api/auth/register/", mismatch, format="json").status_code
        == 400
    )


@pytest.mark.django_db
def test_register_rejects_duplicate_username_and_email(
    api_client, user, register_payload
):
    duplicate_username = {**register_payload, "username": user.username}
    assert (
        api_client.post(
            "/api/auth/register/", duplicate_username, format="json"
        ).status_code
        == 400
    )

    duplicate_email = {**register_payload, "email": user.email}
    assert (
        api_client.post(
            "/api/auth/register/", duplicate_email, format="json"
        ).status_code
        == 400
    )


@pytest.mark.django_db
def test_login_success_and_invalid_credentials(api_client, user):
    success = api_client.post(
        "/api/auth/login/",
        {"username": user.username, "password": PASSWORD},
        format="json",
    )
    assert success.status_code == 200
    assert "access" in success.data
    assert "refresh" in success.data

    wrong_password = api_client.post(
        "/api/auth/login/",
        {"username": user.username, "password": "Wrong#2026"},
        format="json",
    )
    assert wrong_password.status_code == 401
    assert (
        api_client.post(
            "/api/auth/login/",
            {"username": "missing", "password": PASSWORD},
            format="json",
        ).status_code
        == 401
    )


@pytest.mark.django_db
def test_refresh_success_and_invalid_token(api_client, user):
    login = api_client.post(
        "/api/auth/login/",
        {"username": user.username, "password": PASSWORD},
        format="json",
    )
    assert (
        api_client.post(
            "/api/auth/refresh/", {"refresh": login.data["refresh"]}, format="json"
        ).status_code
        == 200
    )
    assert (
        api_client.post(
            "/api/auth/refresh/", {"refresh": "invalid"}, format="json"
        ).status_code
        == 401
    )


@pytest.mark.django_db
def test_logout_requires_authentication_and_does_not_revoke_refresh_token(
    api_client, user
):
    assert api_client.post("/api/auth/logout/").status_code == 401

    login = api_client.post(
        "/api/auth/login/",
        {"username": user.username, "password": PASSWORD},
        format="json",
    )
    api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {login.data['access']}")
    assert api_client.post("/api/auth/logout/").status_code == 204

    api_client.credentials()
    assert (
        api_client.post(
            "/api/auth/refresh/", {"refresh": login.data["refresh"]}, format="json"
        ).status_code
        == 200
    )


@pytest.mark.django_db
def test_profile_requires_valid_token_and_returns_only_current_user(
    api_client, user, access_token
):
    other_user = get_user_model().objects.create_user(
        username="other_user", email="other@example.com", password=PASSWORD
    )

    assert api_client.get("/api/users/me/").status_code == 401
    api_client.credentials(HTTP_AUTHORIZATION="Bearer invalid-token")
    assert api_client.get("/api/users/me/").status_code == 401

    api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {access_token}")
    response = api_client.get("/api/users/me/")
    assert response.status_code == 200
    assert response.data["id"] == user.id
    assert response.data["id"] != other_user.id
