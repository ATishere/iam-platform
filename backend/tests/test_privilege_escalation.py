"""Test spec mục 6: #8, #9, #10, #11."""

import uuid

from fastapi.testclient import TestClient

from tests.conftest import make_admin_token, make_regular_user


def test_user_cannot_escalate_self(client: TestClient) -> None:
    """#9: user tự assign ADMIN cho mình."""
    admin = make_admin_token(client)
    user = make_regular_user(client, admin)
    # Lấy id của user
    r = client.get(
        "/api/v1/users/me",
        headers={"Authorization": f"Bearer {user['access_token']}"},
    )
    uid = r.json()["id"]
    # Lấy id role SUPER_ADMIN
    r = client.get(
        "/api/v1/admin/roles",
        headers={"Authorization": f"Bearer {admin}"},
    )
    super_admin_id = next(
        x["id"] for x in r.json()["items"] if x["name"] == "SUPER_ADMIN"
    )
    # User thường cố gán role
    r = client.put(
        f"/api/v1/admin/users/{uid}/roles",
        headers={"Authorization": f"Bearer {user['access_token']}"},
        json={"role_ids": [super_admin_id]},
    )
    # Không có users:update → 403 ở dependency
    assert r.status_code == 403


def test_admin_cannot_assign_role_with_perms_they_lack(
    client: TestClient,
) -> None:
    """#11: ADMIN (không có roles:manage) không thể assign SUPER_ADMIN cho ai."""
    admin = make_admin_token(client)  # SUPER_ADMIN
    # Tạo 1 ADMIN user
    email_admin = f"admin+{uuid.uuid4().hex[:8]}@example.com"
    pwd = "correct-horse-battery-staple"
    r = client.get(
        "/api/v1/admin/roles",
        headers={"Authorization": f"Bearer {admin}"},
    )
    roles = {x["name"]: x["id"] for x in r.json()["items"]}
    r = client.post(
        "/api/v1/admin/users",
        headers={"Authorization": f"Bearer {admin}"},
        json={
            "email": email_admin,
            "password": pwd,
            "role_ids": [roles["ADMIN"]],
        },
    )
    assert r.status_code == 201, r.text

    # Login as ADMIN
    r = client.post(
        "/api/v1/auth/login",
        json={"email": email_admin, "password": pwd},
    )
    assert r.status_code == 200
    admin2_tok = r.json()["access_token"]

    # Tạo target user
    email_target = f"target+{uuid.uuid4().hex[:8]}@example.com"
    r = client.post(
        "/api/v1/admin/users",
        headers={"Authorization": f"Bearer {admin}"},
        json={"email": email_target, "password": pwd},
    )
    target_uid = r.json()["id"]

    # ADMIN cố assign SUPER_ADMIN cho target → 403 (SUPER_ADMIN có
    # roles:manage mà ADMIN không có)
    r = client.put(
        f"/api/v1/admin/users/{target_uid}/roles",
        headers={"Authorization": f"Bearer {admin2_tok}"},
        json={"role_ids": [roles["SUPER_ADMIN"]]},
    )
    assert r.status_code == 403
    assert "permissions you don't have" in r.json()["detail"]


def test_idor_get_other_org_user(client: TestClient) -> None:
    """#10: IDOR — user cố truy cập user id không tồn tại → 404.

    (MVP single-org nên không test cross-org thật; test nonexistent id.)
    """
    admin = make_admin_token(client)
    r = client.get(
        f"/api/v1/admin/users/{uuid.uuid4()}",
        headers={"Authorization": f"Bearer {admin}"},
    )
    assert r.status_code == 404
