"""FastAPI application entry point."""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1 import auth as auth_router
from app.api.v1 import users as users_router
from app.api.v1.admin import audit as admin_audit_router
from app.api.v1.admin import dashboard as admin_dashboard_router
from app.api.v1.admin import permissions as admin_permissions_router
from app.api.v1.admin import roles as admin_roles_router
from app.api.v1.admin import security as admin_security_router
from app.api.v1.admin import users as admin_users_router
from app.core.config import get_settings
from app.core.logging import configure_logging
from app.core.redis import close_redis, init_redis
from app.db.session import engine


@asynccontextmanager
async def lifespan(app: FastAPI):
    configure_logging()
    await init_redis()
    yield
    await close_redis()
    await engine.dispose()


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(
        title=settings.app_name,
        version="0.4.0-phase4",
        lifespan=lifespan,
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins_list,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.get("/health", tags=["meta"])
    async def health() -> dict[str, str]:
        return {"status": "ok", "phase": "4", "env": settings.app_env}

    app.include_router(auth_router.router, prefix=settings.api_v1_prefix)
    app.include_router(users_router.router, prefix=settings.api_v1_prefix)
    app.include_router(admin_users_router.router, prefix=settings.api_v1_prefix)
    app.include_router(admin_roles_router.router, prefix=settings.api_v1_prefix)
    app.include_router(
        admin_permissions_router.router, prefix=settings.api_v1_prefix
    )
    app.include_router(admin_audit_router.router, prefix=settings.api_v1_prefix)
    app.include_router(
        admin_dashboard_router.router, prefix=settings.api_v1_prefix
    )
    app.include_router(
        admin_security_router.router, prefix=settings.api_v1_prefix
    )

    return app


app = create_app()
