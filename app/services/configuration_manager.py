import os
import secrets
import shutil
import subprocess
from dataclasses import dataclass
from enum import StrEnum
from pathlib import Path
from typing import Protocol

from app.core.config import settings
from app.services.diagnostic_service import DiagnosticReport, DiagnosticStatus
from app.services.environment_manager import EnvironmentCheck, EnvironmentStatus


class SetupStepStatus(StrEnum):
    PENDING = "PENDING"
    RUNNING = "RUNNING"
    OK = "OK"
    WARNING = "WARNING"
    ERROR = "ERROR"


@dataclass(frozen=True, slots=True)
class SetupStepResult:
    key: str
    label: str
    status: SetupStepStatus
    message: str


@dataclass(frozen=True, slots=True)
class SetupReport:
    status: SetupStepStatus
    steps: list[SetupStepResult]
    message: str


@dataclass(frozen=True, slots=True)
class FfmpegStatus:
    configured: bool
    path: str
    message: str


class EnvironmentService(Protocol):
    def prepare(self, install_docker: bool = True) -> EnvironmentCheck:
        pass


class BackendRuntimeService(Protocol):
    def start(self):
        pass


class DiagnosticServiceProtocol(Protocol):
    def run(self) -> DiagnosticReport:
        pass


class EvolutionProvisioningService(Protocol):
    def provision(self) -> SetupStepResult:
        pass


class AppConfigurationManager:
    def __init__(self, project_root: str | Path | None = None) -> None:
        self.project_root = Path(project_root or Path.cwd()).resolve()
        self.env_path = self.project_root / ".env"

    def ensure_defaults(self) -> SetupStepResult:
        values = self._read_env()
        changed = False
        defaults = {
            "APP_NAME": settings.APP_NAME,
            "ENVIRONMENT": settings.ENVIRONMENT,
            "EVOLUTION_BASE_URL": settings.EVOLUTION_BASE_URL,
            "EVOLUTION_INSTANCE": settings.EVOLUTION_INSTANCE,
            "EVOLUTION_TIMEOUT_SECONDS": str(settings.EVOLUTION_TIMEOUT_SECONDS),
            "FILE_STORAGE_ROOT": settings.FILE_STORAGE_ROOT,
            "CONVERSATION_SESSION_TTL_SECONDS": str(settings.CONVERSATION_SESSION_TTL_SECONDS),
            "YOUTUBE_DOWNLOAD_TEMP_ROOT": settings.YOUTUBE_DOWNLOAD_TEMP_ROOT,
            "SQLITE_DATABASE_PATH": settings.SQLITE_DATABASE_PATH,
            "BACKEND_HOST": settings.BACKEND_HOST,
            "BACKEND_PORT": str(settings.BACKEND_PORT),
            "BACKEND_HEALTH_URL": settings.BACKEND_HEALTH_URL,
            "BACKEND_MONITOR_INTERVAL_SECONDS": str(settings.BACKEND_MONITOR_INTERVAL_SECONDS),
            "BACKEND_STARTUP_TIMEOUT_SECONDS": str(settings.BACKEND_STARTUP_TIMEOUT_SECONDS),
            "BACKEND_RESTART_ATTEMPTS": str(settings.BACKEND_RESTART_ATTEMPTS),
        }
        for key, value in defaults.items():
            if not values.get(key):
                values[key] = value
                changed = True

        if not values.get("WEBHOOK_SECRET"):
            values["WEBHOOK_SECRET"] = secrets.token_urlsafe(32)
            changed = True
        if not values.get("EVOLUTION_API_KEY"):
            values["EVOLUTION_API_KEY"] = secrets.token_urlsafe(32)
            changed = True
        values.setdefault("FFMPEG_PATH", settings.FFMPEG_PATH)

        self._sync_runtime_settings(values)
        if changed or not self.env_path.exists():
            self._write_env(values)

        return SetupStepResult(
            key="config",
            label="Configuracoes seguras",
            status=SetupStepStatus.OK,
            message="Configuracoes internas preparadas.",
        )

    def ensure_directories(self) -> SetupStepResult:
        for directory in [
            Path(settings.FILE_STORAGE_ROOT),
            Path(settings.YOUTUBE_DOWNLOAD_TEMP_ROOT),
            Path(settings.SQLITE_DATABASE_PATH).parent,
            Path("logs"),
        ]:
            directory.mkdir(parents=True, exist_ok=True)

        return SetupStepResult(
            key="directories",
            label="Pastas do sistema",
            status=SetupStepStatus.OK,
            message="Pastas criadas e prontas para uso.",
        )

    def set_media_root(self, media_root: str) -> None:
        values = self._read_env()
        values["FILE_STORAGE_ROOT"] = media_root
        settings.FILE_STORAGE_ROOT = media_root
        self._write_env(values)

    def set_ffmpeg_path(self, ffmpeg_path: str) -> None:
        values = self._read_env()
        values["FFMPEG_PATH"] = ffmpeg_path
        settings.FFMPEG_PATH = ffmpeg_path
        self._write_env(values)

    def _read_env(self) -> dict[str, str]:
        if not self.env_path.exists():
            return {}

        values: dict[str, str] = {}
        for line in self.env_path.read_text(encoding="utf-8").splitlines():
            stripped = line.strip()
            if not stripped or stripped.startswith("#") or "=" not in stripped:
                continue
            key, value = stripped.split("=", 1)
            values[key.strip()] = value.strip()
        return values

    def _write_env(self, values: dict[str, str]) -> None:
        content = "\n".join(f"{key}={value}" for key, value in sorted(values.items()))
        self.env_path.write_text(f"{content}\n", encoding="utf-8")

    def _sync_runtime_settings(self, values: dict[str, str]) -> None:
        settings.WEBHOOK_SECRET = values.get("WEBHOOK_SECRET", settings.WEBHOOK_SECRET)
        settings.EVOLUTION_API_KEY = values.get("EVOLUTION_API_KEY", settings.EVOLUTION_API_KEY)
        settings.FILE_STORAGE_ROOT = values.get("FILE_STORAGE_ROOT", settings.FILE_STORAGE_ROOT)
        settings.YOUTUBE_DOWNLOAD_TEMP_ROOT = values.get(
            "YOUTUBE_DOWNLOAD_TEMP_ROOT",
            settings.YOUTUBE_DOWNLOAD_TEMP_ROOT,
        )
        settings.FFMPEG_PATH = values.get("FFMPEG_PATH", settings.FFMPEG_PATH)
        settings.SQLITE_DATABASE_PATH = values.get("SQLITE_DATABASE_PATH", settings.SQLITE_DATABASE_PATH)


class FfmpegManager:
    _CANDIDATE_PATHS = (
        Path("resources") / "ffmpeg.exe",
        Path("resources") / "ffmpeg" / "ffmpeg.exe",
        Path("bin") / "ffmpeg.exe",
        Path("ffmpeg") / "bin" / "ffmpeg.exe",
        Path("ffmpeg") / "ffmpeg.exe",
    )

    def __init__(
        self,
        configuration_manager: AppConfigurationManager | None = None,
        project_root: str | Path | None = None,
        command_runner=subprocess.run,
    ) -> None:
        self.project_root = Path(project_root or Path.cwd()).resolve()
        self._configuration_manager = configuration_manager or AppConfigurationManager(self.project_root)
        self._command_runner = command_runner

    def detect(self) -> FfmpegStatus:
        configured_path = settings.FFMPEG_PATH.strip()
        if configured_path and Path(configured_path).is_file():
            return FfmpegStatus(True, configured_path, "FFmpeg configurado.")

        path_from_env = shutil.which("ffmpeg")
        if path_from_env:
            self._configuration_manager.set_ffmpeg_path(path_from_env)
            return FfmpegStatus(True, path_from_env, "FFmpeg detectado automaticamente.")

        for candidate in self._CANDIDATE_PATHS:
            absolute_candidate = (self.project_root / candidate).resolve()
            if absolute_candidate.is_file():
                self._configuration_manager.set_ffmpeg_path(str(absolute_candidate))
                return FfmpegStatus(True, str(absolute_candidate), "FFmpeg encontrado nos arquivos do YkMedia.")

        return FfmpegStatus(False, "", "FFmpeg ainda nao encontrado.")

    def install(self) -> FfmpegStatus:
        if not shutil.which("winget"):
            return FfmpegStatus(False, "", "Instalacao automatica requer winget no Windows.")

        self._command_runner(
            [
                "winget",
                "install",
                "--id",
                "Gyan.FFmpeg",
                "--exact",
                "--accept-package-agreements",
                "--accept-source-agreements",
                "--silent",
            ],
            capture_output=True,
            text=True,
            check=False,
            timeout=900,
        )
        return self.detect()


class EvolutionProvisioningManager:
    def __init__(
        self,
        evolution_client,
        webhook_url: str | None = None,
        webhook_secret: str | None = None,
    ) -> None:
        self._evolution_client = evolution_client
        self._webhook_url = webhook_url or f"http://host.docker.internal:{settings.BACKEND_PORT}/webhooks/evolution"
        self._webhook_secret = webhook_secret if webhook_secret is not None else settings.WEBHOOK_SECRET

    def provision(self) -> SetupStepResult:
        import asyncio

        try:
            asyncio.run(self._ensure_instance())
            asyncio.run(self._evolution_client.set_webhook(self._webhook_url, self._webhook_secret))
        except Exception as exc:
            return SetupStepResult(
                key="evolution",
                label="Evolution",
                status=SetupStepStatus.ERROR,
                message=f"Nao foi possivel configurar a Evolution: {exc}",
            )

        return SetupStepResult(
            key="evolution",
            label="Evolution",
            status=SetupStepStatus.OK,
            message="Evolution configurada automaticamente.",
        )

    async def _ensure_instance(self) -> None:
        try:
            await self._evolution_client.get_connection_state()
        except Exception:
            await self._evolution_client.create_instance()


class AutomaticSetupService:
    def __init__(
        self,
        configuration_manager: AppConfigurationManager,
        environment_manager: EnvironmentService,
        backend_runtime_manager: BackendRuntimeService,
        evolution_provisioning_manager: EvolutionProvisioningService,
        diagnostic_service: DiagnosticServiceProtocol,
        ffmpeg_manager: FfmpegManager,
    ) -> None:
        self._configuration_manager = configuration_manager
        self._environment_manager = environment_manager
        self._backend_runtime_manager = backend_runtime_manager
        self._evolution_provisioning_manager = evolution_provisioning_manager
        self._diagnostic_service = diagnostic_service
        self._ffmpeg_manager = ffmpeg_manager

    def prepare(self) -> SetupReport:
        steps: list[SetupStepResult] = []
        steps.append(self._configuration_manager.ensure_defaults())
        steps.append(self._configuration_manager.ensure_directories())
        steps.append(self._environment_step())
        steps.append(self._backend_step())
        steps.append(self._evolution_provisioning_manager.provision())
        steps.append(self._ffmpeg_step())
        steps.append(self._diagnostic_step())
        status = self._overall_status(steps)
        message = "Sistema pronto." if status is SetupStepStatus.OK else "Alguns itens ainda precisam de atencao."
        return SetupReport(status=status, steps=steps, message=message)

    def _environment_step(self) -> SetupStepResult:
        check = self._environment_manager.prepare()
        status = SetupStepStatus.OK if check.status is EnvironmentStatus.READY else SetupStepStatus.ERROR
        return SetupStepResult("environment", "Ambiente", status, self._friendly_message(check.message))

    def _backend_step(self) -> SetupStepResult:
        snapshot = self._backend_runtime_manager.start()
        state = getattr(snapshot, "state", None)
        state_value = getattr(state, "value", str(state))
        ok = state_value in {"ONLINE", "STARTING"}
        return SetupStepResult(
            "backend",
            "Backend",
            SetupStepStatus.OK if ok else SetupStepStatus.ERROR,
            "Backend iniciado." if ok else "Nao foi possivel iniciar o backend.",
        )

    def _ffmpeg_step(self) -> SetupStepResult:
        status = self._ffmpeg_manager.detect()
        if not status.configured:
            status = self._ffmpeg_manager.install()
        return SetupStepResult(
            "ffmpeg",
            "FFmpeg",
            SetupStepStatus.OK if status.configured else SetupStepStatus.WARNING,
            status.message,
        )

    def _diagnostic_step(self) -> SetupStepResult:
        report = self._diagnostic_service.run()
        if report.status is DiagnosticStatus.OK:
            status = SetupStepStatus.OK
        elif report.status is DiagnosticStatus.WARNING:
            status = SetupStepStatus.WARNING
        else:
            status = SetupStepStatus.ERROR
        return SetupStepResult("diagnostic", "Teste final", status, report.message)

    def _overall_status(self, steps: list[SetupStepResult]) -> SetupStepStatus:
        if any(step.status is SetupStepStatus.ERROR for step in steps):
            return SetupStepStatus.ERROR
        if any(step.status is SetupStepStatus.WARNING for step in steps):
            return SetupStepStatus.WARNING
        return SetupStepStatus.OK

    def _friendly_message(self, message: str) -> str:
        technical_words = {"Docker", "Compose", "container", "containers"}
        if any(word.lower() in message.lower() for word in technical_words):
            return "Servicos internos preparados."
        return message
