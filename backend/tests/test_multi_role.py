"""Test user có 2 role nhận union permissions (D29, chuyển từ Phase 6)."""

import uuid

from fastapi.testclient import TestClient

from tests.conftest import make_admin_token


def _create_role(client: TestClient, admin: str, code: str) -> str:
    name = f"{code.replace(':', '_').upper()}_{uuid.uuid4().hex[:6].upper()}"
    r = client.post(
        "/api/v1/admin/roles",
        headers={"Authorization": f"Bearer {admin}"},
        json={"name": name, "permission_codes": [code]},
    )
    assert r.status_code == 201, r.text
    return r.json()["id"]


def test_user_with_two_roles_gets_union_permissions(client: TestClient) -> None:
    admin = make_admin_token(client)
    h = {"Authorization": f"Bearer {admin}"}

    role_users_read = _create_role(client, admin, "users:read")
    role_roles_read = _create_role(client, admin, "roles:read")

    email = f"multi+{uuid.uuid4().hex[:8]}@example.com"
    password = "correct-horse-battery-staple"
    r = client.post(
        "/api/v1/admin/users",
        headers=h,
        json={
            "email": email,
            "password": password,
            "role_ids": [role_users_read, role_roles_read],
        },
    )
    assert r.status_code == 201, r.text
    assert len(r.json()["roles"]) == 2

    r = client.post("/api/v1/auth/login", json={"email": email, "password": password})
    assert r.status_code == 200
    user_token = r.json()["access_token"]
    uh = {"Authorization": f"Bearer {user_token}"}

    # Union: users:read từ role 1
    assert client.get("/api/v1/admin/users", headers=uh).status_code == 200
    # Union: roles:read từ role 2
    assert client.get("/api/v1/admin/roles", headers=uh).status_code == 200
    # Không có users:create → 403
    r = client.post(
        "/api/v1/admin/users",
        headers=uh,
        json={
            "email": f"nope+{uuid.uuid4().hex[:6]}@example.com",
            "password": "correct-horse-battery-staple",
        },
    )
    assert r.status_code == 403
