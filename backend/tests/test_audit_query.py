"""Test audit log query API (Phase 4, D37)."""

from fastapi.testclient import TestClient

from tests.conftest import make_admin_token, make_regular_user


def test_audit_logs_listed(client: TestClient) -> None:
    admin = make_admin_token(client)
    r = client.get(
        "/api/v1/admin/audit-logs?page=1&page_size=10",
        headers={"Authorization": f"Bearer {admin}"},
    )
    assert r.status_code == 200
    body = r.json()
    assert body["total"] >= 1
    assert body["page"] == 1 and body["page_size"] == 10
    assert any(item["action"] == "login.success" for item in body["items"])


def test_audit_logs_filter_action(client: TestClient) -> None:
    admin = make_admin_token(client)
    r = client.get(
        "/api/v1/admin/audit-logs?action=login.success",
        headers={"Authorization": f"Bearer {admin}"},
    )
    assert r.status_code == 200
    items = r.json()["items"]
    assert items
    assert all(item["action"] == "login.success" for item in items)


def test_audit_logs_requires_permission(client: TestClient) -> None:
    admin = make_admin_token(client)
    user = make_regular_user(client, admin)
    r = client.get(
        "/api/v1/admin/audit-logs",
        headers={"Authorization": f"Bearer {user['access_token']}"},
    )
    assert r.status_code == 403


def test_security_events_listed(client: TestClient) -> None:
    admin = make_admin_token(client)
    r = client.get(
        "/api/v1/admin/security-events?page=1&page_size=10",
        headers={"Authorization": f"Bearer {admin}"},
    )
    assert r.status_code == 200
    body = r.json()
    assert body["total"] >= 1
    assert body["page"] == 1 and body["page_size"] == 10
    assert any(item["action"] == "login.success" for item in body["items"])


def test_security_events_rejects_non_security_action(client: TestClient) -> None:
    admin = make_admin_token(client)
    r = client.get(
        "/api/v1/admin/security-events?action=user.create",
        headers={"Authorization": f"Bearer {admin}"},
    )
    assert r.status_code == 400


def test_audit_logs_rejects_range_over_90_days(client: TestClient) -> None:
    admin = make_admin_token(client)
    r = client.get(
        "/api/v1/admin/audit-logs",
        headers={"Authorization": f"Bearer {admin}"},
        params={
            "from_date": "2020-01-01T00:00:00",
            "to_date": "2020-06-01T00:00:00",
        },
    )
    assert r.status_code == 400
    assert "90 days" in r.json()["detail"]
