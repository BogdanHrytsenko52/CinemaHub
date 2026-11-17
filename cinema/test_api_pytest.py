import pytest
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient

from cinema.models import Genre


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def staff_user(db):
    return get_user_model().objects.create_user(
        username="staff", password="StrongPassword123!", is_staff=True
    )


@pytest.fixture
def regular_user(db):
    return get_user_model().objects.create_user(
        username="member", password="StrongPassword123!"
    )


@pytest.fixture
def genre(db):
    return Genre.objects.create(name="Science fiction")


@pytest.mark.django_db
def test_genres_are_public_and_staff_can_complete_crud(api_client, staff_user):
    assert api_client.get("/api/genres/").status_code == 200

    api_client.force_authenticate(staff_user)
    created = api_client.post("/api/genres/", {"name": "Drama"}, format="json")
    assert created.status_code == 201
    genre_id = created.data["id"]

    updated = api_client.patch(
        f"/api/genres/{genre_id}/", {"name": "Comedy"}, format="json"
    )
    assert updated.status_code == 200
    assert updated.data["name"] == "Comedy"
    assert api_client.delete(f"/api/genres/{genre_id}/").status_code == 204


@pytest.mark.django_db
def test_genre_write_requires_authentication(api_client):
    response = api_client.post("/api/genres/", {"name": "Drama"}, format="json")
    assert response.status_code == 401


@pytest.mark.django_db
def test_genre_write_rejects_non_staff(api_client, regular_user):
    api_client.force_authenticate(regular_user)
    response = api_client.post("/api/genres/", {"name": "Drama"}, format="json")
    assert response.status_code == 403


@pytest.mark.django_db
def test_genre_rejects_invalid_data_and_missing_resource(api_client, staff_user):
    api_client.force_authenticate(staff_user)
    invalid = api_client.post("/api/genres/", {"name": "   "}, format="json")
    assert invalid.status_code == 400
    assert invalid.data["error"]["code"] == "bad_request"

    missing = api_client.delete("/api/genres/99999/")
    assert missing.status_code == 404
    assert missing.data["error"]["code"] == "not_found"
