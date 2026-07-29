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
from app.services.configuration_manager import AppConfigurationManager, AutomaticSetupService
from app.services.diagnostic_service import DiagnosticService


class SettingsQueryService:
    def __init__(
        self,
        configuration_manager: AppConfigurationManager,
        diagnostic_service: DiagnosticService,
        automatic_setup_service: AutomaticSetupService,
        evolution_client: Any,
    ) -> None:
        self._configuration_manager = configuration_manager
        self._diagnostic_service = diagnostic_service
        self._automatic_setup_service = automatic_setup_service
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
        except Exception as exc:
            return EvolutionSessionResponse(
                instance_name=settings.EVOLUTION_INSTANCE,
                state="Erro",
                message=str(exc),
            )

        return EvolutionSessionResponse(
            instance_name=settings.EVOLUTION_INSTANCE,
            state=self._extract_connection_state(payload),
            qrcode_base64=self._extract_qrcode_base64(payload),
            message="QR Code solicitado.",
        )

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
        candidates = [
            payload.get("base64"),
            payload.get("qrcode"),
            payload.get("qr"),
            payload.get("code"),
        ]
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
            if isinstance(candidate, str) and candidate.strip():
                return candidate
        return None
