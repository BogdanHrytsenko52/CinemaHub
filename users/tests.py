from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.test import APITestCase


class AuthenticationApiTests(APITestCase):
    def registration_payload(self, **overrides):
        data = {
            "username": "cinema_fan",
            "email": "fan@example.com",
            "password": "Strong-password-123",
            "password_confirmation": "Strong-password-123",
        }
        data.update(overrides)
        return data

    def register(self, **overrides):
        return self.client.post(
            "/api/auth/register/", self.registration_payload(**overrides), format="json"
        )

    def test_register_returns_user_and_jwt_tokens(self):
        response = self.register(first_name="Ada", last_name="Lovelace")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["user"]["email"], "fan@example.com")
        self.assertIn("access", response.data)
        self.assertIn("refresh", response.data)
        self.assertTrue(get_user_model().objects.filter(username="cinema_fan").exists())

    def test_registration_validates_required_fields_uniqueness_and_passwords(self):
        self.assertEqual(
            self.client.post("/api/auth/register/", {}, format="json").status_code, 400
        )
        self.register()
        duplicate = self.register(username="other", email="FAN@example.com")
        self.assertEqual(duplicate.status_code, status.HTTP_400_BAD_REQUEST)
        mismatch = self.register(
            username="another",
            email="another@example.com",
            password_confirmation="different",
        )
        self.assertEqual(mismatch.status_code, status.HTTP_400_BAD_REQUEST)

    def test_login_profile_update_and_logout(self):
        registration = self.register()
        login = self.client.post(
            "/api/auth/login/",
            {"username": "cinema_fan", "password": "Strong-password-123"},
            format="json",
        )
        self.assertEqual(login.status_code, status.HTTP_200_OK)
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {login.data['access']}")
        profile = self.client.get("/api/users/me/")
        self.assertEqual(profile.status_code, status.HTTP_200_OK)
        updated = self.client.patch(
            "/api/users/me/",
            {"first_name": "Grace", "email": "grace@example.com"},
            format="json",
        )
        self.assertEqual(updated.status_code, status.HTTP_200_OK)
        self.assertEqual(updated.data["first_name"], "Grace")
        logout = self.client.post(
            "/api/auth/logout/",
            {"refresh": registration.data["refresh"]},
            format="json",
        )
        self.assertEqual(logout.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(
            self.client.post(
                "/api/auth/refresh/",
                {"refresh": registration.data["refresh"]},
                format="json",
            ).status_code,
            status.HTTP_401_UNAUTHORIZED,
        )
