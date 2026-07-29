import asyncio
import sqlite3
from dataclasses import dataclass
from enum import StrEnum
from pathlib import Path
from typing import Protocol

from app.core.config import settings
from app.services.backend_runtime_manager import BackendRuntimeSnapshot, BackendRuntimeState
from app.services.environment_manager import EnvironmentCheck, EnvironmentStatus
from app.services.system_startup_coordinator import StartupReport, StartupStatus


class DiagnosticStatus(StrEnum):
    OK = "OK"
    WARNING = "WARNING"
    ERROR = "ERROR"


@dataclass(frozen=True, slots=True)
class DiagnosticItem:
    key: str
    name: str
    status: DiagnosticStatus
    message: str


@dataclass(frozen=True, slots=True)
class DiagnosticReport:
    status: DiagnosticStatus
    items: list[DiagnosticItem]
    message: str


class EnvironmentService(Protocol):
    def check(self) -> EnvironmentCheck:
        pass

    def prepare(self, install_docker: bool = True) -> EnvironmentCheck:
        pass


class BackendRuntimeService(Protocol):
    def snapshot(self) -> BackendRuntimeSnapshot:
        pass

    def start(self) -> BackendRuntimeSnapshot:
        pass

    def restart(self) -> BackendRuntimeSnapshot:
        pass


class StartupCoordinatorService(Protocol):
    def check(self) -> StartupReport:
        pass

    def prepare(self) -> StartupReport:
        pass


class EvolutionSessionService(Protocol):
    async def get_connection_state(self) -> dict[str, object]:
        pass


class DiagnosticService:
    def __init__(
        self,
        environment_manager: EnvironmentService,
        backend_runtime_manager: BackendRuntimeService,
        startup_coordinator: StartupCoordinatorService,
        evolution_client: EvolutionSessionService,
        media_root: str | Path | None = None,
        sqlite_database: str | Path | None = None,
        ffmpeg_path: str | None = None,
    ) -> None:
        self._environment_manager = environment_manager
        self._backend_runtime_manager = backend_runtime_manager
        self._startup_coordinator = startup_coordinator
        self._evolution_client = evolution_client
        self._media_root = Path(media_root or settings.FILE_STORAGE_ROOT)
        self._sqlite_database = Path(sqlite_database or settings.SQLITE_DATABASE_PATH)
        self._ffmpeg_path = ffmpeg_path if ffmpeg_path is not None else settings.FFMPEG_PATH

    def run(self) -> DiagnosticReport:
        items = [
            self._docker_item(),
            self._containers_item(),
            self._backend_item(),
            self._webhook_item(),
            self._whatsapp_item(),
            self._ffmpeg_item(),
            self._media_root_item(),
            self._sqlite_item(),
        ]
        status = self._overall_status(items)
        return DiagnosticReport(
            status=status,
            items=items,
            message=self._summary_message(status),
        )

    def auto_fix(self) -> DiagnosticReport:
        self._environment_manager.prepare()
        self._backend_runtime_manager.start()
        self._startup_coordinator.prepare()
        return self.run()

    def restart_backend(self) -> DiagnosticReport:
        self._backend_runtime_manager.restart()
        return self.run()

    def _docker_item(self) -> DiagnosticItem:
        check = self._environment_manager.check()
        if check.docker_installed and check.docker_running:
            return DiagnosticItem("docker", "Docker Desktop", DiagnosticStatus.OK, "Docker instalado e em execucao.")
        if not check.docker_installed:
            return DiagnosticItem("docker", "Docker Desktop", DiagnosticStatus.ERROR, "Docker Desktop nao esta instalado.")
        return DiagnosticItem("docker", "Docker Desktop", DiagnosticStatus.ERROR, "Docker instalado, mas parado.")

    def _containers_item(self) -> DiagnosticItem:
        check = self._environment_manager.check()
        if check.status is EnvironmentStatus.READY and check.containers_running:
            return DiagnosticItem("containers", "Containers Evolution", DiagnosticStatus.OK, "Evolution, Postgres e Redis ativos.")
        return DiagnosticItem("containers", "Containers Evolution", DiagnosticStatus.ERROR, check.message)

    def _backend_item(self) -> DiagnosticItem:
        snapshot = self._backend_runtime_manager.snapshot()
        if snapshot.state is BackendRuntimeState.ONLINE:
            return DiagnosticItem("backend", "Backend YkMedia", DiagnosticStatus.OK, "Backend online.")
        if snapshot.state is BackendRuntimeState.STARTING:
            return DiagnosticItem("backend", "Backend YkMedia", DiagnosticStatus.WARNING, "Backend iniciando.")
        return DiagnosticItem(
            "backend",
            "Backend YkMedia",
            DiagnosticStatus.ERROR,
            snapshot.last_error or f"Backend {snapshot.state.value}.",
        )

    def _webhook_item(self) -> DiagnosticItem:
        report = self._startup_coordinator.check()
        if report.status in {StartupStatus.READY, StartupStatus.WHATSAPP_DISCONNECTED}:
            return DiagnosticItem("webhook", "Webhook", DiagnosticStatus.OK, "Webhook local acessivel.")
        if report.status is StartupStatus.WEBHOOK_UNREACHABLE:
            return DiagnosticItem("webhook", "Webhook", DiagnosticStatus.ERROR, report.message)
        return DiagnosticItem("webhook", "Webhook", DiagnosticStatus.WARNING, "Webhook nao verificado: " + report.message)

    def _whatsapp_item(self) -> DiagnosticItem:
        try:
            payload = asyncio.run(self._evolution_client.get_connection_state())
        except Exception as exc:
            return DiagnosticItem("whatsapp", "WhatsApp", DiagnosticStatus.ERROR, f"Falha ao consultar Evolution: {exc}")

        state = self._extract_connection_state(payload)
        if state == "open":
            return DiagnosticItem("whatsapp", "WhatsApp", DiagnosticStatus.OK, "WhatsApp conectado.")
        return DiagnosticItem("whatsapp", "WhatsApp", DiagnosticStatus.WARNING, "WhatsApp desconectado. Gere um QR Code.")

    def _ffmpeg_item(self) -> DiagnosticItem:
        if not self._ffmpeg_path:
            return DiagnosticItem("ffmpeg", "FFmpeg", DiagnosticStatus.WARNING, "FFmpeg nao configurado.")

        path = Path(self._ffmpeg_path)
        if path.exists() and path.is_file():
            return DiagnosticItem("ffmpeg", "FFmpeg", DiagnosticStatus.OK, f"FFmpeg encontrado em {path}.")

        return DiagnosticItem("ffmpeg", "FFmpeg", DiagnosticStatus.ERROR, "Caminho do FFmpeg invalido.")

    def _media_root_item(self) -> DiagnosticItem:
        try:
            self._media_root.mkdir(parents=True, exist_ok=True)
            probe = self._media_root / ".ykmedia-write-test"
            probe.write_text("ok", encoding="utf-8")
            probe.unlink(missing_ok=True)
        except OSError as exc:
            return DiagnosticItem("media_root", "Pasta de midias", DiagnosticStatus.ERROR, f"Sem permissao de escrita: {exc}")

        return DiagnosticItem("media_root", "Pasta de midias", DiagnosticStatus.OK, f"Pasta pronta: {self._media_root.resolve()}.")

    def _sqlite_item(self) -> DiagnosticItem:
        try:
            self._sqlite_database.parent.mkdir(parents=True, exist_ok=True)
            with sqlite3.connect(self._sqlite_database) as connection:
                connection.execute("SELECT 1")
        except sqlite3.Error as exc:
            return DiagnosticItem("sqlite", "Banco SQLite", DiagnosticStatus.ERROR, f"Falha no SQLite: {exc}")
        except OSError as exc:
            return DiagnosticItem("sqlite", "Banco SQLite", DiagnosticStatus.ERROR, f"Falha ao acessar arquivo: {exc}")

        return DiagnosticItem("sqlite", "Banco SQLite", DiagnosticStatus.OK, f"Banco acessivel: {self._sqlite_database.resolve()}.")

    def _extract_connection_state(self, payload: dict[str, object]) -> str:
        instance = payload.get("instance")
        if isinstance(instance, dict):
            value = instance.get("state") or instance.get("status") or instance.get("connectionStatus")
            if value is not None:
                return str(value).lower()

        value = payload.get("state") or payload.get("status") or payload.get("connectionStatus")
        return str(value).lower() if value is not None else "unknown"

    def _overall_status(self, items: list[DiagnosticItem]) -> DiagnosticStatus:
        if any(item.status is DiagnosticStatus.ERROR for item in items):
            return DiagnosticStatus.ERROR
        if any(item.status is DiagnosticStatus.WARNING for item in items):
            return DiagnosticStatus.WARNING
        return DiagnosticStatus.OK

    def _summary_message(self, status: DiagnosticStatus) -> str:
        if status is DiagnosticStatus.OK:
            return "Todos os componentes estao prontos."
        if status is DiagnosticStatus.WARNING:
            return "Sistema funcional, mas ha itens que exigem atencao."
        return "Foram encontrados problemas que podem impedir o funcionamento."
