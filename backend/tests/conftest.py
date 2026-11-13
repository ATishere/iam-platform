"""Fixtures Phase 2: dùng TestClient + DB thật trong container.

Test chạy trong container `backend` → DATABASE_URL đã trỏ postgres service.
Dùng cùng DB dev nhưng test tạo data riêng (email prefix `test+...`).
Phase 6 sẽ tách test DB hoàn toàn.
"""

import os
import sys
import uuid
from collections.abc import Generator

import pytest
from fastapi.testclient import TestClient

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

# Test isolation: rate limit tắt mặc định để test khác không bị 429 do
# dùng chung IP "testclient". test_ratelimit.py bật lại trên Settings instance.
os.environ["RATELIMIT_ENABLED"] = "false"

from app.main import app  # noqa: E402


@pytest.fixture(scope="session")
def client() -> Generator[TestClient, None, None]:
    with TestClient(app) as c:
        yield c


# ---------- Phase 3 helpers ----------


def make_admin_token(client: TestClient) -> str:
    """Đăng nhập seed admin (SUPER_ADMIN), trả access token."""
    email = os.environ["SEED_ADMIN_EMAIL"]
    password = os.environ["SEED_ADMIN_PASSWORD"]
    r = client.post(
        "/api/v1/auth/login", json={"email": email, "password": password}
    )
    assert r.status_code == 200, r.text
    return r.json()["access_token"]


def make_regular_user(client: TestClient, token_admin: str) -> dict:
    """Tạo user thường qua admin endpoint, login, trả token pair."""
    email = f"user+{uuid.uuid4().hex[:10]}@example.com"
    password = "correct-horse-battery-staple"
    r = client.post(
        "/api/v1/admin/users",
        headers={"Authorization": f"Bearer {token_admin}"},
        json={"email": email, "password": password, "full_name": "Regular"},
    )
    assert r.status_code == 201, r.text
    r = client.post(
        "/api/v1/auth/login", json={"email": email, "password": password}
    )
    assert r.status_code == 200
    return {"email": email, "password": password, **r.json()}
