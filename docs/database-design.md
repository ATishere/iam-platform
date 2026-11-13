# Database Design

## ERD (text)

```
organizations 1─* users 1─* sessions 1─* refresh_tokens
organizations 1─* roles 1─* role_permissions *─1 permissions
users 1─* user_roles *─1 roles
users 1─* password_reset_tokens
organizations 1─* audit_logs
```

## Bảng

- **organizations**: tenant boundary (MVP chỉ 1 row).
- **users**: `(organization_id, email)` UNIQUE. `is_locked`, `failed_login_attempts`, `locked_until` cho lockout. Argon2id hash.
- **roles**: `(organization_id, name)` UNIQUE. `is_system` bảo vệ role mặc định.
- **permissions**: catalog global, `code` UNIQUE.
- **user_roles**: M2M user↔role, composite PK.
- **role_permissions**: M2M role↔permission, composite PK.
- **sessions**: `id` = `sid` claim JWT. `is_active` + `revoked_at`.
- **refresh_tokens**: `family_id`, `parent_id`, `replaced_by_id`, `used_at`, `revoked_at` → hỗ trợ reuse detection. `token_hash` UNIQUE.
- **password_reset_tokens**: `token_hash` UNIQUE, single-use, TTL 30 phút.
- **audit_logs**: append-only app-level. `metadata` JSONB.

## Indexes

Mỗi FK có index. `audit_logs(created_at DESC)` sẽ thêm ở Phase 4 khi query
list audit logs (hiện tại index thường đủ cho INSERT).
