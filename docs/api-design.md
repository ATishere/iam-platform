# API Design — Phase 2–4

Base URL: `/api/v1`
Auth: `Authorization: Bearer <access_token>` cho endpoint bảo vệ.

## Endpoints

| Method | Path | Auth | Body | Success |
|--------|------|------|------|---------|
| POST | `/auth/register` | no | `{email, password, full_name?}` | 201 UserRead |
| POST | `/auth/login` | no | `{email, password}` | 200 TokenPair |
| POST | `/auth/refresh` | no | `{refresh_token}` | 200 TokenPair |
| POST | `/auth/logout` | no | `{refresh_token}` | 204 |
| POST | `/auth/change-password` | yes | `{old_password, new_password}` | 204 |
| POST | `/auth/forgot-password` | no | `{email}` | 202 (luôn luôn) |
| POST | `/auth/reset-password` | no | `{token, new_password}` | 204 |
| POST | `/auth/logout-all` | yes | — | 204 (revoke mọi session) |
| GET | `/users/me` | yes | — | 200 UserRead |
| PATCH | `/users/me` | yes | `{full_name?}` | 200 UserRead |
| GET | `/users/me/sessions` | yes | — | 200 SessionRead[] |
| GET | `/health` | no | — | 200 `{status, phase, env}` |

## Admin endpoints (Phase 3)

Tất cả yêu cầu bearer token + permission tương ứng (deny by default).

| Method | Path | Permission | Body / Query | Success |
|--------|------|-----------|--------------|---------|
| GET | `/admin/users` | `users:read` | `?q=&is_active=&page=&page_size=` | 200 `{items,total,page,page_size}` |
| POST | `/admin/users` | `users:create` | `{email,password,full_name?,role_ids?,is_active?}` | 201 UserAdminRead |
| GET | `/admin/users/{id}` | `users:read` | — | 200 / 404 nếu khác org |
| PATCH | `/admin/users/{id}` | `users:update` | `{full_name?,is_active?}` | 200 UserAdminRead |
| DELETE | `/admin/users/{id}` | `users:delete` | — | 204 (soft delete) |
| PUT | `/admin/users/{id}/roles` | `users:update` | `{role_ids}` (full replace) | 200 UserAdminRead |
| DELETE | `/admin/users/{id}/sessions` | `sessions:revoke` | — | 204 |
| GET | `/admin/roles` | `roles:read` | — | 200 `{items,total}` |
| POST | `/admin/roles` | `roles:manage` | `{name,description?,permission_codes?}` | 201 RoleRead |
| PATCH | `/admin/roles/{id}` | `roles:manage` | `{description?}` | 200 RoleRead |
| DELETE | `/admin/roles/{id}` | `roles:manage` | — | 204 / 400 system role / 409 còn user |
| GET | `/admin/permissions` | `roles:read` | — | 200 `{items,total}` |
| GET | `/admin/audit-logs` | `audit:read` | `?action=&actor_id=&resource_type=&resource_id=&outcome=&from_date=&to_date=&page=&page_size=` | 200 `{items,total,page,page_size}` |
| GET | `/admin/security-events` | `audit:read` | `?action=&actor_id=&outcome=&from_date=&to_date=&page=&page_size=` | 200 `{items,total,page,page_size}` |

### Rate limiting (Phase 4)

Áp dụng cho các endpoint public (dependency, không middleware):

| Endpoint | Scope | Default limit |
|----------|-------|---------------|
| `POST /auth/login` | `login:ip` | 10 / 60s |
| `POST /auth/refresh` | `refresh:ip` | 30 / 60s |
| `POST /auth/register` | `register:ip` | 5 / 300s |
| `POST /auth/forgot-password` | `forgot:ip` | 3 / 300s |

Vượt limit → `429` body `{"detail":"Too many requests"}` + header
`Retry-After` (giây). Redis lỗi → **fail-open** (request đi tiếp, log warning).
Env: `RATELIMIT_*` trong `.env.example`.

### Audit query (Phase 4)

- `from_date`/`to_date` nhận ISO-8601; naive datetime được coi là UTC.
  `from_date > to_date` → 400; khoảng cách > **90 ngày** → 400.
- Sort cố định `created_at DESC`; page_size tối đa 100.
- `security-events` chỉ nhận action thuộc catalog security
  (login/refresh/logout/password/session/register); action khác → 400.

### Quy tắc admin

- Mọi thao tác chỉ trong org của actor; target khác org → 404.
- Không xóa/deactivate chính mình (400).
- Không xóa/deactivate SUPER_ADMIN cuối cùng (400).
- Actor chỉ assign role có permissions ⊆ permissions của mình (403).
- `PUT /admin/users/{id}/roles` là **full replace** — phải gửi đủ danh sách
  role hiện tại + thay đổi; gửi `[]` = revoke hết.
- Role `is_system=True` không xóa/sửa tên được; permissions của system role
  chỉ đổi qua seed + migration.


## TokenPair

```json
{
  "access_token": "<jwt>",
  "refresh_token": "<opaque>",
  "token_type": "bearer",
  "access_expires_in": 900,
  "refresh_expires_in": 604800
}
```

## Access token claims

`sub` (user id), `sid` (session id), `org` (organization id), `jti`, `type`
= `access`, `iat`, `exp`. Không chứa permissions (D11).

## Error codes

| Code | Khi nào |
|------|---------|
| 400 | Register email trùng; old password sai; reset token invalid/expired; security-events action không hợp lệ; date range sai |
| 401 | Sai credential; token invalid/expired; session revoked; reuse detected |
| 403 | Account inactive; thiếu permission |
| 423 | Account tạm khoá (quá số lần đăng nhập sai) |
| 429 | Vượt rate limit — kèm header `Retry-After` |
| 503 | Chưa seed organization |

## Hành vi bảo mật

- Login sai → 401 generic (không phân biệt email tồn tại/không).
- Quá `MAX_FAILED_LOGIN_ATTEMPTS` → 423 trong `LOCKOUT_DURATION_MINUTES`.
- Refresh token chỉ dùng 1 lần; dùng lại → 401 và revoke toàn bộ family + session.
- Logout idempotent: refresh token không tồn tại vẫn trả 204.
- Change/reset password revoke mọi session + refresh token của user.
- Forgot-password luôn 202 để chống enumeration.
- Rate limit sliding-window theo IP cho login/refresh/register/forgot
  (Redis); vượt → 429 + `Retry-After`; Redis lỗi → fail-open có log.
- Audit log ghi mọi sự kiện auth (login success/failure/locked, refresh,
  logout, password change/reset), redact key nhạy cảm ở write path.
- Audit/security-events luôn scope theo organization của actor.
