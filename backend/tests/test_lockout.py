"""Test spec mục 6: #2."""

import uuid

from fastapi.testclient import TestClient


def test_account_lockout_after_repeated_failures(client: TestClient) -> None:
    email = f"test+{uuid.uuid4().hex[:10]}@example.com"
    password = "correct-horse-battery-staple"
    client.post(
        "/api/v1/auth/register", json={"email": email, "password": password}
    )

    # 5 lần sai → lock
    for _ in range(5):
        r = client.post(
            "/api/v1/auth/login", json={"email": email, "password": "wrong"}
        )
        assert r.status_code == 401

    # Lần 6: dù password đúng vẫn bị 423
    r = client.post(
        "/api/v1/auth/login", json={"email": email, "password": password}
    )
    assert r.status_code == 423
