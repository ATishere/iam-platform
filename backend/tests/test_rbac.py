"""Test spec mục 6: #7 (user accessing admin endpoints)."""

from fastapi.testclient import TestClient

from tests.conftest import make_admin_token, make_regular_user


def test_regular_user_cannot_list_users(client: TestClient) -> None:
    admin_tok = make_admin_token(client)
    user = make_regular_user(client, admin_tok)
    r = client.get(
        "/api/v1/admin/users",
        headers={"Authorization": f"Bearer {user['access_token']}"},
    )
    assert r.status_code == 403


def test_regular_user_cannot_create_user(client: TestClient) -> None:
    admin_tok = make_admin_token(client)
    user = make_regular_user(client, admin_tok)
    r = client.post(
        "/api/v1/admin/users",
        headers={"Authorization": f"Bearer {user['access_token']}"},
        json={
            "email": "x@example.com",
            "password": "correct-horse-battery-staple",
        },
    )
    assert r.status_code == 403


def test_regular_user_cannot_list_roles(client: TestClient) -> None:
    admin_tok = make_admin_token(client)
    user = make_regular_user(client, admin_tok)
    r = client.get(
        "/api/v1/admin/roles",
        headers={"Authorization": f"Bearer {user['access_token']}"},
    )
    assert r.status_code == 403


def test_admin_can_list_users(client: TestClient) -> None:
    admin_tok = make_admin_token(client)
    r = client.get(
        "/api/v1/admin/users",
        headers={"Authorization": f"Bearer {admin_tok}"},
    )
    assert r.status_code == 200
    body = r.json()
    assert "items" in body and "total" in body


def test_my_permissions(client: TestClient) -> None:
    admin_tok = make_admin_token(client)
    r = client.get(
        "/api/v1/users/me/permissions",
        headers={"Authorization": f"Bearer {admin_tok}"},
    )
    assert r.status_code == 200
    perms = r.json()["permissions"]
    assert "users:read" in perms
    assert "roles:manage" in perms

    user = make_regular_user(client, admin_tok)
    r = client.get(
        "/api/v1/users/me/permissions",
        headers={"Authorization": f"Bearer {user['access_token']}"},
    )
    assert r.status_code == 200
    assert r.json()["permissions"] == []
