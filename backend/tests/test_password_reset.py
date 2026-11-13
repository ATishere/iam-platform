"""Test reset flow. Không test email vì Phase 2 chưa có email service."""

import uuid

from fastapi.testclient import TestClient


def test_forgot_password_always_202(client: TestClient) -> None:
    # Email không tồn tại
    r = client.post(
        "/api/v1/auth/forgot-password",
        json={"email": f"nope+{uuid.uuid4().hex[:8]}@example.com"},
    )
    assert r.status_code == 202


def test_reset_password_invalid_token(client: TestClient) -> None:
    r = client.post(
        "/api/v1/auth/reset-password",
        json={"token": "bogus", "new_password": "a-new-long-password-xx"},
    )
    assert r.status_code == 400
