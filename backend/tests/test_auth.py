"""Happy path + basic auth test. Security edge cases ở file khác."""

import uuid

from fastapi.testclient import TestClient


def _rand_email() -> str:
    return f"test+{uuid.uuid4().hex[:10]}@example.com"


def test_register_login_me(client: TestClient) -> None:
    email = _rand_email()
    password = "correct-horse-battery-staple"

    r = client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": password, "full_name": "Test User"},
    )
    assert r.status_code == 201, r.text

    r = client.post(
        "/api/v1/auth/login", json={"email": email, "password": password}
    )
    assert r.status_code == 200, r.text
    tok = r.json()
    assert tok["token_type"] == "bearer"
    assert tok["access_expires_in"] > 0

    r = client.get(
        "/api/v1/users/me",
        headers={"Authorization": f"Bearer {tok['access_token']}"},
    )
    assert r.status_code == 200
    assert r.json()["email"] == email


def test_login_bad_password(client: TestClient) -> None:
    email = _rand_email()
    client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": "correct-horse-battery-staple"},
    )
    r = client.post(
        "/api/v1/auth/login", json={"email": email, "password": "wrong"}
    )
    assert r.status_code == 401


def test_me_without_token(client: TestClient) -> None:
    r = client.get("/api/v1/users/me")
    assert r.status_code == 401


def test_me_with_garbage_token(client: TestClient) -> None:
    r = client.get(
        "/api/v1/users/me", headers={"Authorization": "Bearer not.a.jwt"}
    )
    assert r.status_code == 401
