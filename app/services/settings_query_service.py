import asyncio
from pathlib import Path
from typing import Any

from app.core.config import settings
from app.models.settings import (
    AppSettingsResponse,
    DiagnosticItemResponse,
    DiagnosticReportResponse,
    EvolutionSessionResponse,
    SaveAppSettingsRequest,
    SetupReportResponse,
    SetupStepResponse,
)
from app.services.configuration_manager import (
    AppConfigurationManager,
    AutomaticSetupService,
    EvolutionProvisioningManager,
    SetupStepStatus,
)
from app.services.evolution_client import EvolutionHttpError
from app.services.diagnostic_service import DiagnosticService


class SettingsQueryService:
    def __init__(
        self,
        configuration_manager: AppConfigurationManager,
        diagnostic_service: DiagnosticService,
        automatic_setup_service: AutomaticSetupService,
        evolution_provisioning_manager: EvolutionProvisioningManager,
        evolution_client: Any,
    ) -> None:
        self._configuration_manager = configuration_manager
        self._diagnostic_service = diagnostic_service
        self._automatic_setup_service = automatic_setup_service
        self._evolution_provisioning_manager = evolution_provisioning_manager
        self._evolution_client = evolution_client

    def get_settings(self) -> AppSettingsResponse:
        evolution = self.get_evolution_session()
        return AppSettingsResponse(
            downloads_root=settings.FILE_STORAGE_ROOT,
            ffmpeg_path=settings.FFMPEG_PATH,
            sqlite_database=settings.SQLITE_DATABASE_PATH,
            whatsapp_instance=settings.EVOLUTION_INSTANCE,
            evolution_state=evolution.state,
            evolution_message=evolution.message,
        )

    def save_settings(self, request: SaveAppSettingsRequest) -> AppSettingsResponse:
        settings.FILE_STORAGE_ROOT = request.downloads_root
        settings.FFMPEG_PATH = request.ffmpeg_path
        settings.SQLITE_DATABASE_PATH = request.sqlite_database
        settings.EVOLUTION_INSTANCE = request.whatsapp_instance
        self._configuration_manager.set_media_root(request.downloads_root)
        if request.ffmpeg_path:
            self._configuration_manager.set_ffmpeg_path(request.ffmpeg_path)
        Path(request.downloads_root).mkdir(parents=True, exist_ok=True)
        return self.get_settings()

    def get_evolution_session(self) -> EvolutionSessionResponse:
        try:
            payload = asyncio.run(self._evolution_client.get_connection_state())
        except Exception as exc:
            return EvolutionSessionResponse(
                instance_name=settings.EVOLUTION_INSTANCE,
                state="Erro",
                message=str(exc),
            )

        return EvolutionSessionResponse(
            instance_name=settings.EVOLUTION_INSTANCE,
            state=self._extract_connection_state(payload),
            message="Estado atualizado.",
        )

    def connect_evolution_session(self) -> EvolutionSessionResponse:
        try:
            payload = asyncio.run(self._evolution_client.connect_instance())
        except EvolutionHttpError as exc:
            if exc.status_code != 404:
                return EvolutionSessionResponse(
                    instance_name=settings.EVOLUTION_INSTANCE,
                    state="Erro",
                    message=str(exc),
                )

            provisioning = self._evolution_provisioning_manager.provision()
            if provisioning.status is not SetupStepStatus.OK:
                return EvolutionSessionResponse(
                    instance_name=settings.EVOLUTION_INSTANCE,
                    state="Erro",
                    message=provisioning.message,
                )

            try:
                payload = asyncio.run(self._evolution_client.connect_instance())
            except Exception as retry_error:
                return EvolutionSessionResponse(
                    instance_name=settings.EVOLUTION_INSTANCE,
                    state="Erro",
                    message=str(retry_error),
                )
        except Exception as exc:
            return EvolutionSessionResponse(
                instance_name=settings.EVOLUTION_INSTANCE,
                state="Erro",
                message=str(exc),
            )

        # /instance/connect nao devolve o estado da sessao, so o QR — sem esta
        # consulta o app mostrava "Desconhecida" mesmo ja estando conectado.
        return EvolutionSessionResponse(
            instance_name=settings.EVOLUTION_INSTANCE,
            state=self._current_connection_state(fallback=payload),
            qrcode_base64=self._extract_qrcode_base64(payload),
            message="QR Code solicitado.",
        )

    def _current_connection_state(self, fallback: dict[str, object]) -> str:
        try:
            state_payload = asyncio.run(self._evolution_client.get_connection_state())
        except Exception:
            return self._extract_connection_state(fallback)

        return self._extract_connection_state(state_payload)

    def disconnect_evolution_session(self) -> EvolutionSessionResponse:
        try:
            payload = asyncio.run(self._evolution_client.logout_instance())
        except Exception as exc:
            return EvolutionSessionResponse(
                instance_name=settings.EVOLUTION_INSTANCE,
                state="Erro",
                message=str(exc),
            )

        return EvolutionSessionResponse(
            instance_name=settings.EVOLUTION_INSTANCE,
            state=self._extract_connection_state(payload) or "close",
            message="Sessao desconectada.",
        )

    def run_diagnostics(self) -> DiagnosticReportResponse:
        report = self._diagnostic_service.run()
        return DiagnosticReportResponse(
            status=report.status.value,
            message=report.message,
            items=[
                DiagnosticItemResponse(
                    key=item.key,
                    name=item.name,
                    status=item.status.value,
                    message=item.message,
                )
                for item in report.items
            ],
        )

    def prepare_system(self) -> SetupReportResponse:
        report = self._automatic_setup_service.prepare()
        return SetupReportResponse(
            status=report.status.value,
            message=report.message,
            steps=[
                SetupStepResponse(
                    key=step.key,
                    label=step.label,
                    status=step.status.value,
                    message=step.message,
                    detail=step.detail,
                    action=step.action,
                )
                for step in report.steps
            ],
        )

    def _extract_connection_state(self, payload: dict[str, object]) -> str:
        instance = payload.get("instance")
        if isinstance(instance, dict):
            value = instance.get("state") or instance.get("status") or instance.get("connectionStatus")
            if value is not None:
                return str(value)
        value = payload.get("state") or payload.get("status") or payload.get("connectionStatus")
        return str(value) if value is not None else "Desconhecida"

    def _extract_qrcode_base64(self, payload: dict[str, object]) -> str | None:
        candidates: list[object] = [payload.get("base64"), payload.get("qrcode"), payload.get("qr"), payload.get("code")]
        instance = payload.get("instance")
        if isinstance(instance, dict):
            candidates.extend(
                [
                    instance.get("base64"),
                    instance.get("qrcode"),
                    instance.get("qr"),
                    instance.get("code"),
                ],
            )
        for candidate in candidates:
            if isinstance(candidate, dict):
                candidates.extend(
                    [
                        candidate.get("base64"),
                        candidate.get("qrcode"),
                        candidate.get("qr"),
                        candidate.get("code"),
                    ]
                )
            if isinstance(candidate, str) and candidate.strip():
                return candidate
        return None
