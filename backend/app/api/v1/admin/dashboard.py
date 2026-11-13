from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps_rbac import require
from app.db.session import get_db
from app.models.user import User
from app.schemas.dashboard import DashboardStats
from app.security.permissions import Permission
from app.services.dashboard_service import DashboardService

router = APIRouter(prefix="/admin/dashboard", tags=["admin:dashboard"])


@router.get("/stats", response_model=DashboardStats)
async def dashboard_stats(
    db: AsyncSession = Depends(get_db),
    actor: User = Depends(require(Permission.USERS_READ)),
) -> DashboardStats:
    svc = DashboardService(db)
    return await svc.get_stats(organization_id=actor.organization_id)
