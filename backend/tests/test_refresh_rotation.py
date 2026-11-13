"""Test spec mục 6: #4, #5, #6, #12."""

import uuid

from fastapi.testclient import TestClient


def _register_and_login(client: TestClient) -> dict:
    email = f"test+{uuid.uuid4().hex[:10]}@example.com"
    password = "correct-horse-battery-staple"
    client.post(
        "/api/v1/auth/register", json={"email": email, "password": password}
    )
    r = client.post(
        "/api/v1/auth/login", json={"email": email, "password": password}
    )
    assert r.status_code == 200
    return r.json()


def test_refresh_rotates(client: TestClient) -> None:
    tok = _register_and_login(client)
    r = client.post(
        "/api/v1/auth/refresh", json={"refresh_token": tok["refresh_token"]}
    )
    assert r.status_code == 200
    new = r.json()
    assert new["refresh_token"] != tok["refresh_token"]
    assert new["access_token"] != tok["access_token"]


def test_refresh_reuse_detected(client: TestClient) -> None:
    """Test #5: dùng lại refresh token cũ → 401 + revoke family."""
    tok = _register_and_login(client)
    old = tok["refresh_token"]
    r1 = client.post("/api/v1/auth/refresh", json={"refresh_token": old})
    assert r1.status_code == 200
    new = r1.json()

    # Reuse old → 401
    r2 = client.post("/api/v1/auth/refresh", json={"refresh_token": old})
    assert r2.status_code == 401

    # New token cũng bị revoke (family revoke)
    r3 = client.post(
        "/api/v1/auth/refresh", json={"refresh_token": new["refresh_token"]}
    )
    assert r3.status_code == 401


def test_refresh_invalid_token(client: TestClient) -> None:
    r = client.post(
        "/api/v1/auth/refresh", json={"refresh_token": "not-a-real-token"}
    )
    assert r.status_code == 401


def test_logout_revokes_session(client: TestClient) -> None:
    tok = _register_and_login(client)
    r = client.post(
        "/api/v1/auth/logout", json={"refresh_token": tok["refresh_token"]}
    )
    assert r.status_code == 204
    # Access token cũ vẫn còn hạn JWT nhưng session đã revoke → 401
    r = client.get(
        "/api/v1/users/me",
        headers={"Authorization": f"Bearer {tok['access_token']}"},
    )
    assert r.status_code == 401
