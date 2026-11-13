"""Smoke test Phase 1: app khởi động và trả /health.

Dùng chung fixture `client` (session-scoped) để lifespan chỉ chạy một lần —
tránh TestClient phụ đóng Redis client toàn cục giữa suite.
"""

from fastapi.testclient import TestClient


def test_health(client: TestClient) -> None:
    resp = client.get("/health")
    assert resp.status_code == 200
    body = resp.json()
    assert body["status"] == "ok"
    assert body["phase"] == "4"
