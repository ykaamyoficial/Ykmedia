from fastapi import APIRouter, Depends

from app.models.dashboard import DashboardOverview
from app.services.application_factory import get_dashboard_service
from app.services.dashboard_service import DashboardService

router = APIRouter(prefix="/dashboard", tags=["dashboard"])


@router.get("/overview", response_model=DashboardOverview)
async def dashboard_overview(
    dashboard_service: DashboardService = Depends(get_dashboard_service),
) -> DashboardOverview:
    return await dashboard_service.get_overview()
