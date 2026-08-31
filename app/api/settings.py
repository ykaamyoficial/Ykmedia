from fastapi import APIRouter, Depends

from app.models.settings import (
    SetupProgressResponse,
    SetupStepResponse,
    AppSettingsResponse,
    DiagnosticReportResponse,
    EvolutionLicenseResponse,
    EvolutionSessionResponse,
    SaveAppSettingsRequest,
    SetupReportResponse,
)
from app.services.application_factory import (
    get_setup_progress_store,
    get_evolution_license_service,
    get_settings_query_service,
)
from app.services.evolution_license_service import EvolutionLicenseService
from app.services.settings_query_service import SettingsQueryService
from app.services.setup_progress import SetupProgressStore

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


@router.get("/prepare/status", response_model=SetupProgressResponse)
def prepare_status(
    store: SetupProgressStore = Depends(get_setup_progress_store),
) -> SetupProgressResponse:
    """Andamento do preparo em curso.

    O POST /prepare demora minutos e so responde no fim; a tela consulta esta
    rota enquanto espera, para mostrar em que etapa o sistema esta.
    """
    snapshot = store.snapshot()
    if snapshot is None:
        return SetupProgressResponse(running=False, status="PENDING", message="", steps=[])

    return SetupProgressResponse(
        running=store.is_running(),
        status=snapshot.status.value,
        message=snapshot.message,
        steps=[
            SetupStepResponse(
                key=step.key,
                label=step.label,
                status=step.status.value,
                message=step.message,
                detail=step.detail,
                action=step.action,
            )
            for step in snapshot.steps
        ],
    )


@router.get("/diagnostics", response_model=DiagnosticReportResponse)
def run_diagnostics(
    service: SettingsQueryService = Depends(get_settings_query_service),
) -> DiagnosticReportResponse:
    return service.run_diagnostics()


@router.get("/evolution/license", response_model=EvolutionLicenseResponse)
def get_evolution_license(
    service: EvolutionLicenseService = Depends(get_evolution_license_service),
) -> EvolutionLicenseResponse:
    state = service.status()
    return EvolutionLicenseResponse(status=state.status.value, message=state.message)


@router.post("/evolution/license/register", response_model=EvolutionLicenseResponse)
def start_evolution_license_registration(
    service: EvolutionLicenseService = Depends(get_evolution_license_service),
) -> EvolutionLicenseResponse:
    state = service.start_registration()
    return EvolutionLicenseResponse(
        status=state.status.value,
        register_url=state.register_url,
        message=state.message,
    )
