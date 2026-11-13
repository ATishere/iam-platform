"""Test Redis rate limiting (Phase 4, D32–D35)."""

import uuid

import pytest
from fastapi.testclient import TestClient

from app.core.config import get_settings


@pytest.fixture(autouse=True)
def _ratelimit_test_env(monkeypatch: pytest.MonkeyPatch):
    """Bật rate limit + prefix riêng cho từng test.

    Patch trực tiếp Settings instance đang cache để không phải clear cache
    (tránh rò rỉ trạng thái sang test khác).
    """
    settings = get_settings()
    monkeypatch.setattr(settings, "ratelimit_enabled", True)
    monkeypatch.setattr(
        settings, "ratelimit_key_prefix", f"iam:rl:test:{uuid.uuid4().hex}"
    )
    monkeypatch.setattr(settings, "ratelimit_login_ip_limit", 3)
    monkeypatch.setattr(settings, "ratelimit_login_ip_window", 60)
    yield


def test_login_rate_limit(client: TestClient) -> None:
    email = f"rl+{uuid.uuid4().hex[:8]}@example.com"
    password = "correct-horse-battery-staple"
    r = client.post(
        "/api/v1/auth/register", json={"email": email, "password": password}
    )
    assert r.status_code == 201, r.text

    for _ in range(3):
        r = client.post(
            "/api/v1/auth/login",
            json={"email": email, "password": "wrong-password"},
        )
        assert r.status_code == 401, r.text

    r = client.post(
        "/api/v1/auth/login", json={"email": email, "password": "wrong-password"}
    )
    assert r.status_code == 429
    assert r.json()["detail"] == "Too many requests"
    assert "retry-after" in {k.lower() for k in r.headers}
