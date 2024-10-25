from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient


TOKEN_URL = reverse("user:token_obtain_pair")

User = get_user_model()


class TokenTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            email="test@test.com",
            password="testpass"
        )

    def test_obtain_token(self):
        data = {
            "email": "test@test.com",
            "password": "testpass",
        }
        response = self.client.post(TOKEN_URL, data)
        self.assertEqual(response.status_code, 200)
        self.assertIn("access", response.data)
        self.assertIn("refresh", response.data)

    def test_refresh_token(self):
        data = {
            "email": "test@test.com",
            "password": "testpass",
        }
        response = self.client.post(TOKEN_URL, data)
        refresh_token = response.data["refresh"]
        response = self.client.post(
            reverse("user:token_refresh"),
            {"refresh": refresh_token}
        )
        self.assertEqual(response.status_code, 200)
        self.assertIn("access", response.data)

    def test_verify_token(self):
        data = {
            "email": "test@test.com",
            "password": "testpass",
        }
        response = self.client.post(TOKEN_URL, data)
        access_token = response.data["access"]
        response = self.client.post(
            reverse("user:token_verify"), {"token": access_token}
        )
        self.assertEqual(response.status_code, 200)
