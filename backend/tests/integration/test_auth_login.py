from __future__ import annotations

import pytest
from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework.test import APIClient

User = get_user_model()


@pytest.mark.django_db
def test_login_and_me_flow():
    User.objects.create_user(username="admin", password="admin123", email="admin@example.com")
    client = APIClient()

    response = client.post("/api/auth/login", {"username": "admin", "password": "admin123"}, format="json")
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "Bearer"
    assert data["user"]["username"] == "admin"

    token = data["access_token"]
    client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")
    profile_response = client.get("/api/auth/profile")
    assert profile_response.status_code == 200
    profile_data = profile_response.json()
    assert profile_data["username"] == "admin"


@pytest.mark.django_db
def test_login_invalid_credentials():
    User.objects.create_user(username="admin", password="admin123")
    client = APIClient()

    response = client.post("/api/auth/login", {"username": "admin", "password": "wrong"}, format="json")
    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid credentials"
