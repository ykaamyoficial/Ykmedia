import asyncio
import logging
from dataclasses import dataclass
from enum import StrEnum
from typing import Protocol
from urllib.error import URLError
from urllib.request import Request, urlopen

from app.core.config import settings
from app.services.backend_runtime_manager import BackendRuntimeSnapshot, BackendRuntimeState
from app.services.environment_manager import EnvironmentCheck, EnvironmentStatus

logger = logging.getLogger(__name__)


class StartupStatus(StrEnum):
    CHECKING = "CHECKING"
    READY = "READY"
    DOCKER_MISSING = "DOCKER_MISSING"
    DOCKER_STOPPED = "DOCKER_STOPPED"
    CONTAINERS_ERROR = "CONTAINERS_ERROR"
    BACKEND_ERROR = "BACKEND_ERROR"
    WEBHOOK_UNREACHABLE = "WEBHOOK_UNREACHABLE"
    WHATSAPP_DISCONNECTED = "WHATSAPP_DISCONNECTED"
    ERROR = "ERROR"


class StartupStepStatus(StrEnum):
    PENDING = "PENDING"
    OK = "OK"
    WARNING = "WARNING"
    ERROR = "ERROR"


@dataclass(frozen=True, slots=True)
class StartupStep:
    name: str
    status: StartupStepStatus
    message: str


@dataclass(frozen=True, slots=True)
class StartupReport:
    status: StartupStatus
    steps: list[StartupStep]
    is_ready: bool
    message: str


class EnvironmentService(Protocol):
    def check(self) -> EnvironmentCheck:
        pass

    def prepare(self, install_docker: bool = True) -> EnvironmentCheck:
        pass


class BackendRuntimeService(Protocol):
    def start(self) -> BackendRuntimeSnapshot:
        pass

    def snapshot(self) -> BackendRuntimeSnapshot:
        pass


class EvolutionSessionService(Protocol):
    async def get_connection_state(self) -> dict[str, object]:
        pass


class SystemStartupCoordinator:
    def __init__(
        self,
        environment_manager: EnvironmentService,
        backend_runtime_manager: BackendRuntimeService,
        evolution_client: EvolutionSessionService,
        webhook_url: str | None = None,
        webhook_secret: str | None = None,
        webhook_checker=None,
    ) -> None:
        self._environment_manager = environment_manager
        self._backend_runtime_manager = backend_runtime_manager
        self._evolution_client = evolution_client
        self._webhook_url = webhook_url or self._default_webhook_url()
        self._webhook_secret = webhook_secret if webhook_secret is not None else settings.WEBHOOK_SECRET
        self._webhook_checker = webhook_checker or self._default_webhook_checker

    def check(self) -> StartupReport:
        logger.info("Verificando inicializacao do sistema YkMedia.")
        environment = self._environment_manager.check()
        return self._build_report(environment=environment)

    def prepare(self) -> StartupReport:
        logger.info("Preparando inicializacao completa do sistema YkMedia.")
        environment = self._environment_manager.prepare()
        return self._build_report(environment=environment)

    def _build_report(
        self,
        environment: EnvironmentCheck,
    ) -> StartupReport:
        steps: list[StartupStep] = []

        environment_status = self._environment_step(environment)
        steps.append(environment_status)
        if environment_status.status is StartupStepStatus.ERROR:
            return self._report_from_environment_error(environment, steps)

        backend_snapshot = self._backend_runtime_manager.start()
        backend_step = self._backend_step(backend_snapshot)
        steps.append(backend_step)
        if backend_step.status is StartupStepStatus.ERROR:
            return StartupReport(
                status=StartupStatus.BACKEND_ERROR,
                steps=steps,
                is_ready=False,
                message=backend_step.message,
            )

        webhook_step = self._webhook_step()
        steps.append(webhook_step)
        if webhook_step.status is StartupStepStatus.ERROR:
            return StartupReport(
                status=StartupStatus.WEBHOOK_UNREACHABLE,
                steps=steps,
                is_ready=False,
                message=webhook_step.message,
            )

        whatsapp_step = self._whatsapp_step()
        steps.append(whatsapp_step)
        if whatsapp_step.status is StartupStepStatus.WARNING:
            return StartupReport(
                status=StartupStatus.WHATSAPP_DISCONNECTED,
                steps=steps,
                is_ready=False,
                message=whatsapp_step.message,
            )
        if whatsapp_step.status is StartupStepStatus.ERROR:
            return StartupReport(
                status=StartupStatus.ERROR,
                steps=steps,
                is_ready=False,
                message=whatsapp_step.message,
            )

        return StartupReport(
            status=StartupStatus.READY,
            steps=steps,
            is_ready=True,
            message="Sistema pronto para receber midias pelo WhatsApp.",
        )

    def _environment_step(self, environment: EnvironmentCheck) -> StartupStep:
        if environment.status is EnvironmentStatus.READY:
            return StartupStep("Docker e containers", StartupStepStatus.OK, environment.message)
        if environment.status is EnvironmentStatus.CONFIG_MISSING:
            return StartupStep("Docker e containers", StartupStepStatus.ERROR, environment.message)
        if environment.status is EnvironmentStatus.DOCKER_MISSING:
            return StartupStep("Docker", StartupStepStatus.ERROR, environment.message)
        if environment.status is EnvironmentStatus.DOCKER_STOPPED:
            return StartupStep("Docker", StartupStepStatus.ERROR, environment.message)

        return StartupStep("Docker e containers", StartupStepStatus.ERROR, environment.message)

    def _report_from_environment_error(
        self,
        environment: EnvironmentCheck,
        steps: list[StartupStep],
    ) -> StartupReport:
        status = StartupStatus.CONTAINERS_ERROR
        if environment.status is EnvironmentStatus.DOCKER_MISSING:
            status = StartupStatus.DOCKER_MISSING
        elif environment.status is EnvironmentStatus.DOCKER_STOPPED:
            status = StartupStatus.DOCKER_STOPPED

        return StartupReport(
            status=status,
            steps=steps,
            is_ready=False,
            message=environment.message,
        )

    def _backend_step(self, snapshot: BackendRuntimeSnapshot) -> StartupStep:
        if snapshot.state in {BackendRuntimeState.ONLINE, BackendRuntimeState.STARTING}:
            return StartupStep("Backend FastAPI", StartupStepStatus.OK, f"Backend {snapshot.state.value}.")

        message = snapshot.last_error or f"Backend {snapshot.state.value}."
        return StartupStep("Backend FastAPI", StartupStepStatus.ERROR, message)

    def _webhook_step(self) -> StartupStep:
        try:
            reachable = self._webhook_checker(self._webhook_url, self._webhook_secret)
        except Exception as exc:
            logger.warning("Falha ao testar webhook local: %s", exc)
            reachable = False

        if reachable:
            return StartupStep("Webhook", StartupStepStatus.OK, "Webhook local acessivel.")

        return StartupStep(
            "Webhook",
            StartupStepStatus.ERROR,
            "A Evolution nao consegue acessar o webhook local do YkMedia.",
        )

    def _whatsapp_step(self) -> StartupStep:
        try:
            payload = asyncio.run(self._evolution_client.get_connection_state())
        except Exception as exc:
            return StartupStep("WhatsApp", StartupStepStatus.ERROR, f"Falha ao consultar Evolution: {exc}")

        state = self._extract_connection_state(payload)
        if state == "open":
            return StartupStep("WhatsApp", StartupStepStatus.OK, "WhatsApp conectado.")

        return StartupStep("WhatsApp", StartupStepStatus.WARNING, "WhatsApp desconectado. Gere um QR Code para conectar.")

    def _extract_connection_state(self, payload: dict[str, object]) -> str:
        instance = payload.get("instance")
        if isinstance(instance, dict):
            value = instance.get("state") or instance.get("status") or instance.get("connectionStatus")
            if value is not None:
                return str(value).lower()

        value = payload.get("state") or payload.get("status") or payload.get("connectionStatus")
        return str(value).lower() if value is not None else "unknown"

    def _default_webhook_url(self) -> str:
        return f"http://localhost:{settings.BACKEND_PORT}/webhooks/evolution"

    def _default_webhook_checker(self, url: str, webhook_secret: str) -> bool:
        headers = {"Content-Type": "application/json"}
        if webhook_secret:
            headers["x-webhook-secret"] = webhook_secret

        body = b'{"event":"startup.check","data":{}}'
        request = Request(url=url, data=body, headers=headers, method="POST")
        try:
            with urlopen(request, timeout=3.0) as response:
                return response.status < 500
        except (OSError, URLError):
            return False
