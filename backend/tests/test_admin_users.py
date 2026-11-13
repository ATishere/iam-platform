"""Test admin CRUD + pagination + search."""

import uuid

from fastapi.testclient import TestClient

from tests.conftest import make_admin_token


def test_create_and_get_user(client: TestClient) -> None:
    admin = make_admin_token(client)
    email = f"new+{uuid.uuid4().hex[:8]}@example.com"
    r = client.post(
        "/api/v1/admin/users",
        headers={"Authorization": f"Bearer {admin}"},
        json={
            "email": email,
            "password": "correct-horse-battery-staple",
            "full_name": "New User",
        },
    )
    assert r.status_code == 201
    uid = r.json()["id"]

    r = client.get(
        f"/api/v1/admin/users/{uid}",
        headers={"Authorization": f"Bearer {admin}"},
    )
    assert r.status_code == 200
    assert r.json()["email"] == email


def test_list_users_pagination(client: TestClient) -> None:
    admin = make_admin_token(client)
    r = client.get(
        "/api/v1/admin/users?page=1&page_size=5",
        headers={"Authorization": f"Bearer {admin}"},
    )
    assert r.status_code == 200
    body = r.json()
    assert body["page"] == 1 and body["page_size"] == 5
    assert len(body["items"]) <= 5


def test_search_users(client: TestClient) -> None:
    admin = make_admin_token(client)
    email = f"searchme+{uuid.uuid4().hex[:8]}@example.com"
    client.post(
        "/api/v1/admin/users",
        headers={"Authorization": f"Bearer {admin}"},
        json={"email": email, "password": "correct-horse-battery-staple"},
    )
    r = client.get(
        "/api/v1/admin/users?q=searchme",
        headers={"Authorization": f"Bearer {admin}"},
    )
    assert r.status_code == 200
    assert any(email == u["email"] for u in r.json()["items"])


def test_delete_user_soft(client: TestClient) -> None:
    admin = make_admin_token(client)
    email = f"del+{uuid.uuid4().hex[:8]}@example.com"
    r = client.post(
        "/api/v1/admin/users",
        headers={"Authorization": f"Bearer {admin}"},
        json={"email": email, "password": "correct-horse-battery-staple"},
    )
    uid = r.json()["id"]
    r = client.delete(
        f"/api/v1/admin/users/{uid}",
        headers={"Authorization": f"Bearer {admin}"},
    )
    assert r.status_code == 204
    # User vẫn tồn tại nhưng inactive
    r = client.get(
        f"/api/v1/admin/users/{uid}",
        headers={"Authorization": f"Bearer {admin}"},
    )
    assert r.status_code == 200
    assert r.json()["is_active"] is False


def test_cannot_delete_self(client: TestClient) -> None:
    admin = make_admin_token(client)
    r = client.get(
        "/api/v1/users/me",
        headers={"Authorization": f"Bearer {admin}"},
    )
    me = r.json()["id"]
    r = client.delete(
        f"/api/v1/admin/users/{me}",
        headers={"Authorization": f"Bearer {admin}"},
    )
    assert r.status_code == 400
