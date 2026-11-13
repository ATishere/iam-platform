"""Test redaction: helper + audit API không lộ secrets (Phase 4, D39)."""

import uuid

from fastapi.testclient import TestClient

from app.security.audit import redact
from tests.conftest import make_admin_token


def test_redact_recursive_payload() -> None:
    data = {
        "email": "a@example.com",
        "password": "hunter2",
        "nested": {"refresh_token": "abc", "keep": 1},
        "items": [{"authorization": "Bearer xyz"}],
        "message": "failed with Bearer abc.def.ghi",
    }
    out = redact(data)
    assert out["password"] == "[REDACTED]"
    assert out["nested"]["refresh_token"] == "[REDACTED]"
    assert out["nested"]["keep"] == 1
    assert out["items"][0]["authorization"] == "[REDACTED]"
    assert "abc.def.ghi" not in out["message"]


def test_redaction_in_audit_log(client: TestClient) -> None:
    admin = make_admin_token(client)
    plain_password = "correct-horse-battery-staple"
    email = f"redact+{uuid.uuid4().hex[:8]}@example.com"
    r = client.post(
        "/api/v1/admin/users",
        headers={"Authorization": f"Bearer {admin}"},
        json={"email": email, "password": plain_password},
    )
    assert r.status_code == 201
    uid = r.json()["id"]

    r = client.get(
        f"/api/v1/admin/audit-logs?action=user.create&resource_id={uid}",
        headers={"Authorization": f"Bearer {admin}"},
    )
    assert r.status_code == 200
    items = r.json()["items"]
    assert items
    meta = items[0]["metadata"]
    assert "password" not in meta
    assert "password_hash" not in meta
    assert plain_password not in r.text
