from fastapi import APIRouter, Depends

from app.models.settings import (
    AppSettingsResponse,
    DiagnosticReportResponse,
    EvolutionSessionResponse,
    SaveAppSettingsRequest,
    SetupReportResponse,
)
from app.services.application_factory import get_settings_query_service
from app.services.settings_query_service import SettingsQueryService

router = APIRouter(prefix="/settings", tags=["settings"])


@router.get("", response_model=AppSettingsResponse)
def get_settings(service: SettingsQueryService = Depends(get_settings_query_service)) -> AppSettingsResponse:
    return service.get_settings()


@router.put("", response_model=AppSettingsResponse)
def save_settings(
    request: SaveAppSettingsRequest,
    service: SettingsQueryService = Depends(get_settings_query_service),
) -> AppSettingsResponse:
    return service.save_settings(request)


@router.get("/evolution", response_model=EvolutionSessionResponse)
def get_evolution_session(
    service: SettingsQueryService = Depends(get_settings_query_service),
) -> EvolutionSessionResponse:
    return service.get_evolution_session()


@router.post("/evolution/connect", response_model=EvolutionSessionResponse)
def connect_evolution_session(
    service: SettingsQueryService = Depends(get_settings_query_service),
) -> EvolutionSessionResponse:
    return service.connect_evolution_session()


@router.post("/evolution/disconnect", response_model=EvolutionSessionResponse)
def disconnect_evolution_session(
    service: SettingsQueryService = Depends(get_settings_query_service),
) -> EvolutionSessionResponse:
    return service.disconnect_evolution_session()


@router.post("/prepare", response_model=SetupReportResponse)
def prepare_system(service: SettingsQueryService = Depends(get_settings_query_service)) -> SetupReportResponse:
    return service.prepare_system()


@router.get("/diagnostics", response_model=DiagnosticReportResponse)
def run_diagnostics(
    service: SettingsQueryService = Depends(get_settings_query_service),
) -> DiagnosticReportResponse:
    return service.run_diagnostics()
