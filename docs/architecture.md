# Architecture

## Decisions

### Phase 1

| ID | Decision | Rationale |
|----|----------|-----------|
| D1 | `organization_id` trên mọi bảng tenant-scoped | Tenant-ready; thêm sau rất đắt |
| D2 | UUID v4 cho mọi PK | Tránh IDOR enumeration |
| D3 | Refresh token family chain | Reuse detection (spec test #5, #12) |
| D4 | `sessions.id` = `sid` JWT claim; 1 session → N refresh tokens | Rotation chain theo session |
| D5 | `TIMESTAMPTZ`, `datetime.now(timezone.utc)` | UTC everywhere |
| D6 | Argon2id full string trong `password_hash` | Format chuẩn đã chứa params |
| D7 | Audit append-only ở app layer (MVP) | Spec chỉ yêu cầu app-level |
| D8 | pydantic-settings + fail-fast nếu thiếu secret | Không hardcode |
| D9 | pip + requirements.txt | User yêu cầu |
| D10 | python:3.12-slim, postgres:16-alpine, redis:7-alpine | Ổn định, nhỏ |

### Phase 2

| ID | Decision | Rationale |
|----|----------|-----------|
| D11 | Access token claims: `sub/sid/org/jti/iat/exp/type` — **không** chứa permissions | Token nhỏ; permission check ở server (Phase 3) |
| D12 | Refresh token opaque `secrets.token_urlsafe(48)`; DB lưu `sha256` hex | Không thể dùng token từ DB dump; deterministic hash để lookup |
| D13 | Rotation + reuse detection: `SELECT ... FOR UPDATE`, reuse → revoke cả family + session | Chống đánh cắp refresh token |
| D14 | Session lifecycle: login tạo session; logout/change-password/reset revoke session; access token chết ngay khi session revoke | Revoke không cần chờ JWT hết hạn |
| D15 | Lockout: 5 lần sai → khoá 15 phút (`locked_until` = source of truth, `is_locked` = cache) | Chống brute force; tự mở khoá khi hết hạn |
| D16 | Forgot-password luôn trả 202, không tiết lộ email tồn tại | Chống user enumeration |
| D17 | Password: 12–128 ký tự, không chỉ whitespace | Theo NIST/OWASP baseline |
| D18 | Register trả 400 generic khi email trùng | Không tiết lộ email đã tồn tại |
| D19 | Seed idempotent bằng script từ env (`SEED_ADMIN_EMAIL`, `SEED_ADMIN_PASSWORD`) | Không hardcode credential trong code |
| D20 | Audit append-only cho mọi auth event; redact key nhạy cảm trước khi ghi | Truy vết; không lộ secret |

### Phase 3

| ID | Decision | Rationale |
|----|----------|-----------|
| D21 | Permission resolution per-request: load user + roles + permissions bằng JOIN từ DB; **không cache Redis** | Đơn giản, đúng, dễ test; 3 JOIN nhỏ/request chấp nhận được cho MVP. Cache sớm = bug invalidation khi revoke role (tech debt Phase 4) |
| D22 | `require(*permissions)` = AND, `require_any(*permissions)` = OR; route admin **phải** khai báo permission | Deny by default: route không khai báo chỉ cần auth; admin route thiếu khai báo là lỗi review |
| D23 | Privilege escalation prevention: actor chỉ assign role có permissions ⊆ permissions của actor, cùng organization; không revoke `SUPER_ADMIN` nếu actor không phải `SUPER_ADMIN`; không tự revoke `SUPER_ADMIN` cuối cùng; không gán role cross-org | Spec test #9, #11 |
| D24 | IDOR prevention: mọi route `admin/users/{user_id}` load user rồi check `organization_id == actor.organization_id`; khác → **404** (không phải 403) | Defense-in-depth chống enumeration. Spec test #10 |
| D25 | Delete user = soft delete (`is_active=False`), revoke toàn bộ session + refresh token; không xoá chính mình; không xoá `SUPER_ADMIN` cuối cùng | Giữ audit trail/integrity; hard delete làm mất lịch sử |
| D26 | Role management: `POST` tạo role `is_system=False`; `PATCH` chỉ update `description`; `DELETE` không cho role `is_system=True`, không cho role còn user gán (409); role phải cùng org với actor | Spec mục Role & Permission |
| D27 | Permission catalog chỉ read-only `GET /admin/permissions` (không POST/PATCH/DELETE) | Permission là catalog seed, không phải resource người dùng |
| D28 | Audit events Phase 3: `user.create/update/delete/activate/deactivate`, `role.create/update/delete`, `user.roles.assign/revoke`, `session.revoke`, `auth.logout_all` — `actor_id` = admin, `resource_id` = target | Truy vết thay đổi quyền |
| D29 | Pagination chuẩn `?page=1&page_size=20` (max 100); response `{items,total,page,page_size}`; search `?q=` (email/full_name ILIKE); filter `?is_active=`, `?role=` | Spec mục C |
| D30 | `POST /admin/users` admin set password trực tiếp (policy ≥ 12 ký tự); không auto-generate/trả về | Phase 2 chưa có email service; Phase 4+ chuyển invite flow |
| D31 | Fix Phase 2: (1) generate `family_id = uuid4()` trước khi tạo `RefreshToken`; (2) guard log reset token: `APP_ENV != production`, production → `RuntimeError`; (3) thêm `/auth/logout-all` | Sửa bug nhỏ gây confusing; fail loud thay vì silent |

### Phase 4

| ID | Decision | Rationale |
|----|----------|-----------|
| D32 | Rate limit sliding window bằng Redis sorted set + Lua atomic (`ZREMRANGEBYSCORE` → `ZADD` → `ZCARD` → `PEXPIRE`) | Chính xác hơn fixed window, không burst ở biên; Lua đảm bảo atomic |
| D33 | Scope hiện enforce: `login:ip`, `register:ip`, `refresh:ip`, `forgot:ip`. Account/email scopes (`login:account`, `forgot:email`) chưa dùng vì dependency chưa parse body | Tech debt — xem Known tech debt |
| D34 | Key = `{RATELIMIT_KEY_PREFIX}:{scope}:{sha256(identity)[:32]}` | Không lưu IP/email plaintext trong Redis |
| D35 | 429 body `{"detail":"Too many requests"}` + header `Retry-After` (giây, tính từ entry cũ nhất trong window) | Chuẩn HTTP, client backoff đúng |
| D36 | Permission resolution vẫn per-request, **không cache Redis** (giữ D21); rate limiter là consumer Redis duy nhất của auth flow | Tránh invalidation bug; rate limit độc lập với permission |
| D37 | `GET /admin/audit-logs` filter `action/actor_id/resource_type/resource_id/outcome/from_date/to_date`, sort `created_at DESC`, pagination chuẩn; luôn scope theo `actor.organization_id` | Truy vết; không lộ log org khác |
| D38 | `GET /admin/security-events` chỉ trả `_SECURITY_ACTIONS` (auth/session); `action` ngoài set → 400 | Tách "security events" khỏi audit chung |
| D39 | Redaction chạy ở write path (`AuditRepository.insert` → `redact()`), query chỉ đọc dữ liệu đã redact | Một chỗ enforce, không quên ở read path |
| D40 | Rate limit dùng FastAPI dependency (`dependencies=[Depends(...)]`), không middleware | Route khai báo tường minh; test bật/tắt dễ; 429 cùng format lỗi API |
| D41 | `RATELIMIT_ENABLED` + env tunables (limit/window từng scope). Test mặc định tắt qua `conftest.py`; `test_ratelimit.py` patch Settings instance với prefix riêng từng test | TestClient dùng chung IP `testclient` → tránh 429 chéo test |
| D42 | Fail-open: Redis chưa init/lỗi `EVAL` → cho request đi qua + log `WARNING`; không chặn auth flow | Availability > strictness cho MVP; giám sát qua log |
| D43 | Audit query giới hạn khoảng `from_date`–`to_date` tối đa **90 ngày** (400 nếu vượt); `from_date > to_date` → 400 | Chặn query nặng; bảo vệ DB khi log tăng |

## Known tech debt

- **Audit log DB-level immutability chưa có.** Chỉ enforce ở repository
  (không có method update/delete). Nếu reviewer yêu cầu, thêm trigger hoặc
  revoke UPDATE/DELETE grants — không làm ở MVP.
- **Chưa có email service.** Forgot-password log raw token ra stdout khi
  `APP_ENV != production`; production raise `RuntimeError` (fail loud).
- **Account-level login rate limit (5/60s theo email) và `forgot:email`
  chưa enforce** — dependency không đọc được body trước khi parse; IP-level
  đã có. Quyết định: làm ở Phase 6 (service-level sau khi parse body).
- **Security events pre-auth chỉ log stdlib** (`security.invalid_jwt`,
  `security.session_inactive`, `security.ratelimit_exceeded`) vì
  `audit_logs.organization_id` NOT NULL và chưa có system org. Quyết định:
  giữ log, không đổi schema ở MVP.
- **Permission check vẫn chạy 1 query JOIN mỗi request, chưa cache** sau
  Phase 4 (D36). Nếu performance test fail → thêm Redis cache + invalidation
  khi `set_roles`/`set_permissions`.
- **Rate limit fail-open khi Redis down** (D42) — đã chốt giữ cho MVP;
  Redis sự cố không làm sập auth, theo dõi qua log `WARNING`.
- **`GET /admin/users/{id}/sessions` chưa có.** Spec chỉ yêu cầu
  `/users/me/sessions`.
- **`PUT /admin/users/{id}/roles` là full replace** (không phải add/remove
  delta). Frontend phải load current roles trước khi gửi; audit log cho phép
  recover.
- **Role `is_system=True` không update được permissions qua API** — đúng
  thiết kế; thay đổi qua seed + migration.
- **Chưa test #8 cross-user** — Phase 6. Multi-role union đã test ở Phase 4.
- **`get_default_organization` lấy org đầu tiên** — MVP single-org. Admin
  routes dùng `actor.organization_id`, đã tenant-ready.
- **Chưa có test concurrent refresh race** — logic đã dùng `FOR UPDATE`,
  test đồng thời để Phase 6.
- **Chưa có CI.** Phase 6.
- **Chưa có tenant management UI/endpoint.** Chỉ có 1 org mặc định seed tay.

## Module layout

```
app/
  api/          deps, deps_rbac, deps_ratelimit,
                v1/{auth,users}, v1/admin/{users,roles,permissions,audit,security}
  core/         config, logging, redis
  db/           Base, engine, session
  models/       SQLAlchemy ORM
  schemas/      Pydantic request/response (auth, user, admin, audit)
  services/     auth_service, user_admin_service, role_service, audit_service
  repositories/ data access (user, session, refresh_token, password_reset, audit,
                role, permission)
  security/     password (argon2), tokens (jwt/opaque), audit (redact),
                permissions (catalog), ratelimit (sliding window)
  scripts/      seed
  main.py
```

## Auth flow

```
login ──► create session + refresh token (family_id = uuid4())
            │
            ├─ access token (JWT 15m, sid=session.id)
            └─ refresh token (opaque 7d)

refresh ──► SELECT refresh_tokens FOR UPDATE
            ├─ revoked/used? → revoke family + session → 401
            ├─ expired? → 401
            └─ ok → mark used, create next token (same family), new access
```

Mọi request có access token → `get_current_user` kiểm tra session còn active
trong DB (revoke session = token chết ngay).

## Authorization flow (Phase 3)

```
request ──► get_current_user (session + user active)
              │
              └─► require(Permission.X) / require_any(...)
                    │
                    └─► get_user_permissions(user, db)
                          permission_codes JOIN role_permissions
                          JOIN roles JOIN user_roles
                          WHERE user_id = user.id
                            AND role.organization_id = user.organization_id
                          │
                          ├─ missing → 403
                          └─ ok → actor = User
```

## Rate limiting flow (Phase 4)

```
request ──► Depends(rate_limit_{login,register,refresh,forgot}_ip)
              │
              ├─ RATELIMIT_ENABLED=false → skip
              └─► Redis EVAL sliding window(scope, sha256(client_ip))
                    ├─ count > limit → 429 + Retry-After
                    └─ ok / Redis lỗi → fail-open, request đi tiếp
```

Defaults: login/ip 10/60s, refresh/ip 30/60s, register/ip 5/300s,
forgot/ip 3/300s. Key TTL = window + 1s.

## Audit query flow (Phase 4)

```
GET /admin/audit-logs ──► require(audit:read)
  ──► AuditService.query_logs
        WHERE organization_id = actor.organization_id
        + optional filters (action/actor/resource/outcome/date range)
        ORDER BY created_at DESC, pagination

GET /admin/security-events ──► require(audit:read)
  ──► action ∉ _SECURITY_ACTIONS → 400
  ──► query (IN _SECURITY_ACTIONS) hoặc query theo action cụ thể
```
