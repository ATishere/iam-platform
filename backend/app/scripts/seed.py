"""Seed dữ liệu mặc định — idempotent, chạy lại an toàn.

Usage (trong container):
    docker compose exec backend python -m app.scripts.seed

Env bắt buộc:
    SEED_ADMIN_EMAIL
    SEED_ADMIN_PASSWORD (>= 12 ký tự)
"""

import asyncio
import os
import sys

from sqlalchemy import select

from app.db.session import AsyncSessionLocal
from app.models.organization import Organization
from app.models.permission import Permission
from app.models.role import Role
from app.models.role_permission import RolePermission
from app.models.user import User
from app.models.user_role import UserRole
from app.security.password import hash_password

PERMISSIONS: list[tuple[str, str]] = [
    ("users:read", "Read user information"),
    ("users:create", "Create users"),
    ("users:update", "Update users"),
    ("users:delete", "Delete users"),
    ("roles:read", "Read roles"),
    ("roles:manage", "Manage roles and permissions"),
    ("audit:read", "Read audit logs"),
    ("sessions:revoke", "Revoke user sessions"),
]

ROLE_PERMISSIONS: dict[str, list[str]] = {
    "SUPER_ADMIN": [p for p, _ in PERMISSIONS],  # all
    "ADMIN": [
        "users:read",
        "users:create",
        "users:update",
        "users:delete",
        "roles:read",
        "audit:read",
        "sessions:revoke",
    ],
    "DEVELOPER": ["users:read", "roles:read"],
    "ANALYST": ["users:read"],
    "USER": [],
}


async def seed() -> None:
    admin_email = os.environ.get("SEED_ADMIN_EMAIL")
    admin_password = os.environ.get("SEED_ADMIN_PASSWORD")
    if not admin_email or not admin_password:
        print(
            "ERROR: SEED_ADMIN_EMAIL and SEED_ADMIN_PASSWORD must be set.",
            file=sys.stderr,
        )
        sys.exit(1)
    if len(admin_password) < 12:
        print("ERROR: SEED_ADMIN_PASSWORD must be >= 12 chars.", file=sys.stderr)
        sys.exit(1)

    async with AsyncSessionLocal() as db:
        # 1. Organization
        org = (
            await db.execute(
                select(Organization).where(Organization.slug == "default")
            )
        ).scalar_one_or_none()
        if org is None:
            org = Organization(name="Default Organization", slug="default")
            db.add(org)
            await db.flush()
            print(f"[seed] created organization {org.id}")
        else:
            print(f"[seed] organization exists {org.id}")

        # 2. Permissions
        perm_map: dict[str, Permission] = {}
        for code, desc in PERMISSIONS:
            p = (
                await db.execute(select(Permission).where(Permission.code == code))
            ).scalar_one_or_none()
            if p is None:
                p = Permission(code=code, description=desc)
                db.add(p)
                await db.flush()
                print(f"[seed] created permission {code}")
            perm_map[code] = p

        # 3. Roles + role_permissions
        role_map: dict[str, Role] = {}
        for role_name, perm_codes in ROLE_PERMISSIONS.items():
            r = (
                await db.execute(
                    select(Role).where(
                        Role.organization_id == org.id, Role.name == role_name
                    )
                )
            ).scalar_one_or_none()
            if r is None:
                r = Role(
                    organization_id=org.id,
                    name=role_name,
                    is_system=True,
                )
                db.add(r)
                await db.flush()
                print(f"[seed] created role {role_name}")
            role_map[role_name] = r

            for code in perm_codes:
                exists = (
                    await db.execute(
                        select(RolePermission).where(
                            RolePermission.role_id == r.id,
                            RolePermission.permission_id == perm_map[code].id,
                        )
                    )
                ).scalar_one_or_none()
                if exists is None:
                    db.add(
                        RolePermission(
                            role_id=r.id, permission_id=perm_map[code].id
                        )
                    )

        # 4. Admin user
        admin = (
            await db.execute(
                select(User).where(
                    User.organization_id == org.id,
                    User.email == admin_email.lower(),
                )
            )
        ).scalar_one_or_none()
        if admin is None:
            admin = User(
                organization_id=org.id,
                email=admin_email.lower(),
                full_name="Seed Super Admin",
                password_hash=hash_password(admin_password),
                is_active=True,
            )
            db.add(admin)
            await db.flush()
            print(f"[seed] created admin user {admin.email}")
        else:
            print(f"[seed] admin user exists {admin.email}")

        # 5. Assign SUPER_ADMIN to admin
        has_role = (
            await db.execute(
                select(UserRole).where(
                    UserRole.user_id == admin.id,
                    UserRole.role_id == role_map["SUPER_ADMIN"].id,
                )
            )
        ).scalar_one_or_none()
        if has_role is None:
            db.add(
                UserRole(
                    user_id=admin.id, role_id=role_map["SUPER_ADMIN"].id
                )
            )
            print("[seed] assigned SUPER_ADMIN to admin")

        await db.commit()
        print("[seed] done.")


if __name__ == "__main__":
    asyncio.run(seed())
