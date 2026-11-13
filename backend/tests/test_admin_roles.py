import uuid

from fastapi.testclient import TestClient

from tests.conftest import make_admin_token


def test_list_roles_and_permissions(client: TestClient) -> None:
    admin = make_admin_token(client)
    r = client.get(
        "/api/v1/admin/roles",
        headers={"Authorization": f"Bearer {admin}"},
    )
    assert r.status_code == 200
    names = [role["name"] for role in r.json()["items"]]
    assert "SUPER_ADMIN" in names

    r = client.get(
        "/api/v1/admin/permissions",
        headers={"Authorization": f"Bearer {admin}"},
    )
    assert r.status_code == 200
    codes = [p["code"] for p in r.json()["items"]]
    assert "users:read" in codes


def test_create_custom_role(client: TestClient) -> None:
    admin = make_admin_token(client)
    name = f"ROLE_{uuid.uuid4().hex[:6].upper()}"
    r = client.post(
        "/api/v1/admin/roles",
        headers={"Authorization": f"Bearer {admin}"},
        json={
            "name": name,
            "description": "Test role",
            "permission_codes": ["users:read"],
        },
    )
    assert r.status_code == 201, r.text
    assert r.json()["name"] == name
    assert r.json()["permission_codes"] == ["users:read"]


def test_cannot_delete_system_role(client: TestClient) -> None:
    admin = make_admin_token(client)
    r = client.get(
        "/api/v1/admin/roles",
        headers={"Authorization": f"Bearer {admin}"},
    )
    super_admin = next(
        x for x in r.json()["items"] if x["name"] == "SUPER_ADMIN"
    )
    r = client.delete(
        f"/api/v1/admin/roles/{super_admin['id']}",
        headers={"Authorization": f"Bearer {admin}"},
    )
    assert r.status_code == 400
