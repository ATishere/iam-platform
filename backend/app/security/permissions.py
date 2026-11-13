"""Canonical permission catalog — đồng bộ với seed script.

Nếu thêm permission mới: thêm ở đây + seed.py PERMISSIONS + migration
nếu cần backfill role_permissions.
"""

from enum import StrEnum


class Permission(StrEnum):
    USERS_READ = "users:read"
    USERS_CREATE = "users:create"
    USERS_UPDATE = "users:update"
    USERS_DELETE = "users:delete"
    ROLES_READ = "roles:read"
    ROLES_MANAGE = "roles:manage"
    AUDIT_READ = "audit:read"
    SESSIONS_REVOKE = "sessions:revoke"


ALL_PERMISSIONS: frozenset[str] = frozenset(p.value for p in Permission)
