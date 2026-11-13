from fastapi.testclient import TestClient

from tests.conftest import make_admin_token, make_regular_user


def test_dashboard_stats_admin(client: TestClient) -> None:
    admin = make_admin_token(client)
    r = client.get(
        "/api/v1/admin/dashboard/stats",
        headers={"Authorization": f"Bearer {admin}"},
    )
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["users_total"] >= 1
    assert body["users_active"] >= 1
    assert body["users_locked"] >= 0
    assert body["recent_logins_24h"] >= 1
    assert "recent_security_events" in body
    assert isinstance(body["recent_security_events"], list)


def test_dashboard_requires_permission(client: TestClient) -> None:
    admin = make_admin_token(client)
    user = make_regular_user(client, admin)
    r = client.get(
        "/api/v1/admin/dashboard/stats",
        headers={"Authorization": f"Bearer {user['access_token']}"},
    )
    assert r.status_code == 403
