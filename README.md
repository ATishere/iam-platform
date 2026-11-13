# IAM Platform

Identity and Access Management system for internal AI platform.

## Tech Stack
- Backend: Python 3.12, FastAPI, SQLAlchemy 2.0 (async), PostgreSQL 16, Redis 7, Alembic
- Frontend: Next.js (Phase 5)
- Infra: Docker Compose, Pytest, GitHub Actions

## Local Setup

### 1. Yêu cầu
- Docker Desktop
- Python 3.12+ (nếu chạy backend ngoài Docker)

### 2. Cấu hình
```bash
cp .env.example .env
# Sửa .env: đổi SECRET_KEY, POSTGRES_PASSWORD, DATABASE_URL,
# SEED_ADMIN_EMAIL, SEED_ADMIN_PASSWORD
```

Generate SECRET_KEY:
```bash
python -c "import secrets; print(secrets.token_urlsafe(64))"
```

### 3. Chạy
```bash
docker compose up -d --build
```

Backend: http://localhost:8000
API docs: http://localhost:8000/docs
Health: http://localhost:8000/health

### 4. Migration
```bash
docker compose exec backend alembic upgrade head
```

### 5. Seed dữ liệu mặc định
```bash
docker compose exec backend python -m app.scripts.seed
```

Seed idempotent — chạy lại an toàn. Tạo: org `default`, 8 permissions,
5 roles (SUPER_ADMIN, ADMIN, DEVELOPER, ANALYST, USER), admin user từ
`SEED_ADMIN_EMAIL` / `SEED_ADMIN_PASSWORD`.

### 6. Test
```bash
docker compose exec backend pytest -q
```

## Trạng thái triển khai
- [x] Phase 1: Foundation (models, migrations, config, docker)
- [x] Phase 2: Authentication (JWT, refresh rotation, lockout, password reset)
- [x] Phase 3: Authorization (RBAC) — roles, permissions, admin API
- [x] Phase 4: Security & Audit — Redis rate limiting, audit query, security events
- [ ] Phase 5: Frontend
- [ ] Phase 6: Quality & Delivery

> Phase 4: rate limit sliding-window (Redis) cho login/refresh/register/forgot,
> `GET /admin/audit-logs` + `GET /admin/security-events` (filter + pagination),
> redaction test, multi-role union test. Redis lỗi → rate limit fail-open.

## Cấu trúc
Xem `docs/architecture.md` và `docs/api-design.md`.
