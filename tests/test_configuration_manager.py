from pathlib import Path

from app.services.backend_runtime_manager import BackendRuntimeSnapshot, BackendRuntimeState
from app.services.configuration_manager import (
    AppConfigurationManager,
    AutomaticSetupService,
    EvolutionProvisioningManager,
    FfmpegManager,
    SetupStepResult,
    SetupStepStatus,
)
from app.services.diagnostic_service import DiagnosticReport, DiagnosticStatus
from app.services.environment_manager import EnvironmentCheck, EnvironmentStatus
from app.services.evolution_client import EvolutionConnectionError, EvolutionHttpError


class FakeEnvironmentManager:
    def prepare(self, install_docker: bool = True) -> EnvironmentCheck:
        return EnvironmentCheck(
            status=EnvironmentStatus.READY,
            docker_installed=True,
            docker_running=True,
            compose_available=True,
            containers_running=True,
            message="containers ativos",
        )


class FakeBackendRuntimeManager:
    def start(self) -> BackendRuntimeSnapshot:
        return BackendRuntimeSnapshot(
            state=BackendRuntimeState.ONLINE,
            health_url="http://localhost:8010/health",
            managed_process=True,
            restart_attempts=0,
            last_error=None,
        )


class FakeDiagnosticService:
    def run(self) -> DiagnosticReport:
        return DiagnosticReport(status=DiagnosticStatus.OK, items=[], message="Todos os componentes estao prontos.")


class FakeEvolutionProvisioning:
    def provision(self) -> SetupStepResult:
        return SetupStepResult("evolution", "Evolution", SetupStepStatus.OK, "Evolution configurada.")


class FakeEvolutionClient:
    def __init__(self, connection_fails: bool = False) -> None:
        self.connection_fails = connection_fails
        self.created = False
        self.webhook_url = ""

    async def get_connection_state(self) -> dict[str, object]:
        if self.connection_fails:
            raise EvolutionHttpError(404, "Evolution API returned HTTP 404.")
        return {"instance": {"state": "open"}}

    async def create_instance(self) -> dict[str, object]:
        self.created = True
        return {"instance": {"instanceName": "ykmedia"}}

    async def set_webhook(self, url: str, webhook_secret: str = "", events: list[str] | None = None) -> dict[str, object]:
        self.webhook_url = url
        return {"webhook": {"enabled": True}}


class DelayedEvolutionClient(FakeEvolutionClient):
    def __init__(self) -> None:
        super().__init__()
        self.attempts = 0

    async def get_connection_state(self) -> dict[str, object]:
        self.attempts += 1
        if self.attempts == 1:
            raise EvolutionConnectionError("starting")
        return {"instance": {"state": "open"}}


class UnexpectedEvolutionErrorClient(FakeEvolutionClient):
    async def get_connection_state(self) -> dict[str, object]:
        raise EvolutionHttpError(500, "Evolution API returned HTTP 500.")


def test_configuration_manager_creates_env_and_directories(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    manager = AppConfigurationManager(project_root=tmp_path)

    config = manager.ensure_defaults()
    directories = manager.ensure_directories()

    env_content = (tmp_path / ".env").read_text(encoding="utf-8")
    assert config.status is SetupStepStatus.OK
    assert directories.status is SetupStepStatus.OK
    assert "WEBHOOK_SECRET=" in env_content
    assert "EVOLUTION_API_KEY=" in env_content
    assert (tmp_path / "media").exists()
    assert (tmp_path / "data").exists()


def test_ffmpeg_manager_detects_project_binary(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr("app.services.configuration_manager.shutil.which", lambda command: None)
    ffmpeg = tmp_path / "bin" / "ffmpeg.exe"
    ffmpeg.parent.mkdir()
    ffmpeg.write_text("fake", encoding="utf-8")
    manager = AppConfigurationManager(project_root=tmp_path)

    status = FfmpegManager(configuration_manager=manager, project_root=tmp_path).detect()

    assert status.configured is True
    assert status.path == str(ffmpeg.resolve())


def test_evolution_provisioning_creates_missing_instance_and_sets_webhook() -> None:
    client = FakeEvolutionClient(connection_fails=True)
    manager = EvolutionProvisioningManager(client, webhook_url="http://host.docker.internal:8010/webhooks/evolution")

    result = manager.provision()

    assert result.status is SetupStepStatus.OK
    assert client.created is True
    assert client.webhook_url == "http://host.docker.internal:8010/webhooks/evolution"


def test_evolution_provisioning_retries_while_api_is_starting() -> None:
    client = DelayedEvolutionClient()
    delays: list[float] = []
    manager = EvolutionProvisioningManager(
        client,
        readiness_attempts=2,
        retry_delay_seconds=0.1,
        sleep=delays.append,
    )

    result = manager.provision()

    assert result.status is SetupStepStatus.OK
    assert client.attempts == 2
    assert delays == [0.1]


def test_evolution_provisioning_does_not_create_instance_after_unexpected_http_error() -> None:
    client = UnexpectedEvolutionErrorClient()
    manager = EvolutionProvisioningManager(client, readiness_attempts=1)

    result = manager.provision()

    assert result.status is SetupStepStatus.ERROR
    assert client.created is False


def test_automatic_setup_orchestrates_all_steps(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    configuration = AppConfigurationManager(project_root=tmp_path)
    ffmpeg = tmp_path / "bin" / "ffmpeg.exe"
    ffmpeg.parent.mkdir()
    ffmpeg.write_text("fake", encoding="utf-8")

    report = AutomaticSetupService(
        configuration_manager=configuration,
        environment_manager=FakeEnvironmentManager(),
        backend_runtime_manager=FakeBackendRuntimeManager(),
        evolution_provisioning_manager=FakeEvolutionProvisioning(),
        diagnostic_service=FakeDiagnosticService(),
        ffmpeg_manager=FfmpegManager(configuration_manager=configuration, project_root=tmp_path),
    ).prepare()

    assert report.status is SetupStepStatus.OK
    assert [step.key for step in report.steps] == [
        "config",
        "directories",
        "environment",
        "backend",
        "evolution",
        "ffmpeg",
        "diagnostic",
    ]
