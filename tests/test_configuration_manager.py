import subprocess
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
            raise RuntimeError("missing")
        return {"instance": {"state": "open"}}

    async def create_instance(self) -> dict[str, object]:
        self.created = True
        return {"instance": {"instanceName": "ykmedia"}}

    async def set_webhook(self, url: str, webhook_secret: str = "", events: list[str] | None = None) -> dict[str, object]:
        self.webhook_url = url
        return {"webhook": {"enabled": True}}


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
