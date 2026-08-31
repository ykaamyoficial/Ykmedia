import json
from pathlib import Path

from app.services.backend_runtime_manager import BackendRuntimeSnapshot, BackendRuntimeState
from app.core.config import settings
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
from app.services.evolution_license_service import LicenseState, LicenseStatus



class FakeLicenseService:
    def __init__(self, status: LicenseStatus) -> None:
        self._status = status

    def status(self) -> LicenseState:
        return LicenseState(status=self._status, message=f"licenca {self._status.value}")


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
    # settings.FFMPEG_PATH vem do .env: rodar o app a partir do repo cria um e
    # o teste passava a detectar o FFmpeg da maquina em vez do de tmp_path.
    monkeypatch.setattr(settings, "FFMPEG_PATH", "")
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
        license_service=FakeLicenseService(LicenseStatus.ACTIVE),
    ).prepare()

    assert report.status is SetupStepStatus.OK
    assert [step.key for step in report.steps] == [
        "config",
        "directories",
        "environment",
        "backend",
        "license",
        "evolution",
        "ffmpeg",
        "diagnostic",
    ]


def test_setup_stops_before_provisioning_when_license_is_pending(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    configuration = AppConfigurationManager(project_root=tmp_path)
    provisioning = FakeEvolutionProvisioning()

    report = AutomaticSetupService(
        configuration_manager=configuration,
        environment_manager=FakeEnvironmentManager(),
        backend_runtime_manager=FakeBackendRuntimeManager(),
        evolution_provisioning_manager=provisioning,
        diagnostic_service=FakeDiagnosticService(),
        ffmpeg_manager=FfmpegManager(configuration_manager=configuration, project_root=tmp_path),
        license_service=FakeLicenseService(LicenseStatus.PENDING),
    ).prepare()

    license_step = next(step for step in report.steps if step.key == "license")
    assert license_step.status is SetupStepStatus.ERROR
    assert "Ativar licenca" in license_step.message
    # Sem licenca a Evolution responde 503: nao adianta provisionar. A etapa
    # continua visivel como Aguardando -- esconde-la deixaria o usuario sem
    # saber que ela existe e por que nao rodou.
    evolution_step = next(step for step in report.steps if step.key == "evolution")
    assert evolution_step.status is SetupStepStatus.PENDING
    assert "Licenca" in evolution_step.message
    assert report.status is SetupStepStatus.ERROR


def test_setup_accepts_versions_without_licensing(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    configuration = AppConfigurationManager(project_root=tmp_path)

    report = AutomaticSetupService(
        configuration_manager=configuration,
        environment_manager=FakeEnvironmentManager(),
        backend_runtime_manager=FakeBackendRuntimeManager(),
        evolution_provisioning_manager=FakeEvolutionProvisioning(),
        diagnostic_service=FakeDiagnosticService(),
        ffmpeg_manager=FfmpegManager(configuration_manager=configuration, project_root=tmp_path),
        license_service=FakeLicenseService(LicenseStatus.NOT_REQUIRED),
    ).prepare()

    assert next(s for s in report.steps if s.key == "license").status is SetupStepStatus.OK
    assert "evolution" in [step.key for step in report.steps]


class FailingEnvironmentManager:
    """Reproduz a maquina do usuario: o compose rodou, os containers nao subiram."""

    def prepare(self, install_docker: bool = True) -> EnvironmentCheck:
        return EnvironmentCheck(
            status=EnvironmentStatus.ERROR,
            docker_installed=True,
            docker_running=True,
            compose_available=True,
            containers_running=False,
            message=(
                "Docker Compose executou, mas nem todos os containers ficaram ativos:\n"
                "ykmedia_evolution Exited (1)"
            ),
        )


def test_environment_failure_keeps_the_real_reason(tmp_path: Path, monkeypatch) -> None:
    """O motivo da falha nao pode ser trocado pelo texto de sucesso.

    Era o que a tela do usuario mostrava: a etapa Ambiente em ERROR com a
    mensagem "Servicos internos preparados.". `_friendly_message` substituia
    qualquer texto com a palavra "Docker" ou "container" -- inclusive os erros --
    deixando o problema impossivel de diagnosticar.
    """
    monkeypatch.chdir(tmp_path)
    configuration = AppConfigurationManager(project_root=tmp_path)

    report = AutomaticSetupService(
        configuration_manager=configuration,
        environment_manager=FailingEnvironmentManager(),
        backend_runtime_manager=FakeBackendRuntimeManager(),
        evolution_provisioning_manager=FakeEvolutionProvisioning(),
        diagnostic_service=FakeDiagnosticService(),
        ffmpeg_manager=FfmpegManager(configuration_manager=configuration, project_root=tmp_path),
        license_service=FakeLicenseService(LicenseStatus.ACTIVE),
    ).prepare()

    environment = next(step for step in report.steps if step.key == "environment")
    assert environment.status is SetupStepStatus.ERROR
    assert "Servicos internos preparados" not in environment.message
    assert "ykmedia_evolution" in environment.message


def test_evolution_steps_are_skipped_when_the_environment_failed(tmp_path: Path, monkeypatch) -> None:
    """Sem containers, licenca e Evolution so produzem erros derivados.

    Na tela do usuario apareciam tres erros para uma causa unica, escondendo
    qual deles precisava de acao.
    """
    monkeypatch.chdir(tmp_path)
    configuration = AppConfigurationManager(project_root=tmp_path)

    report = AutomaticSetupService(
        configuration_manager=configuration,
        environment_manager=FailingEnvironmentManager(),
        backend_runtime_manager=FakeBackendRuntimeManager(),
        evolution_provisioning_manager=FakeEvolutionProvisioning(),
        diagnostic_service=FakeDiagnosticService(),
        ffmpeg_manager=FfmpegManager(configuration_manager=configuration, project_root=tmp_path),
        license_service=FakeLicenseService(LicenseStatus.ACTIVE),
    ).prepare()

    evolution_step = next(step for step in report.steps if step.key == "evolution")
    assert evolution_step.status is SetupStepStatus.PENDING
    license_step = next(step for step in report.steps if step.key == "license")
    assert license_step.status is SetupStepStatus.PENDING
    assert "ambiente" in license_step.message.lower()


class SlowLicenseService:
    """A Evolution roda migracoes: leva dezenas de segundos ate atender HTTP."""

    def __init__(self, attempts_until_ready: int) -> None:
        self._attempts_until_ready = attempts_until_ready
        self.attempts = 0

    def status(self) -> LicenseState:
        self.attempts += 1
        if self.attempts < self._attempts_until_ready:
            return LicenseState(
                status=LicenseStatus.UNAVAILABLE,
                message="Nao foi possivel falar com a Evolution.",
            )
        return LicenseState(status=LicenseStatus.ACTIVE, message="licenca ativa")


def test_license_waits_for_evolution_to_answer(tmp_path: Path, monkeypatch) -> None:
    """`compose up` termina antes da Evolution atender.

    Consultar a licenca no mesmo instante devolvia UNAVAILABLE e a tela acusava
    "Nao foi possivel falar com a Evolution" num ambiente que ficava pronto
    logo em seguida.
    """
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr("app.services.configuration_manager.time.sleep", lambda _: None)
    configuration = AppConfigurationManager(project_root=tmp_path)
    license_service = SlowLicenseService(attempts_until_ready=4)

    report = AutomaticSetupService(
        configuration_manager=configuration,
        environment_manager=FakeEnvironmentManager(),
        backend_runtime_manager=FakeBackendRuntimeManager(),
        evolution_provisioning_manager=FakeEvolutionProvisioning(),
        diagnostic_service=FakeDiagnosticService(),
        ffmpeg_manager=FfmpegManager(configuration_manager=configuration, project_root=tmp_path),
        license_service=license_service,
    ).prepare()

    license_step = next(step for step in report.steps if step.key == "license")
    assert license_step.status is SetupStepStatus.OK
    assert license_service.attempts >= 4


def test_a_single_cause_produces_a_single_red_item(tmp_path: Path, monkeypatch) -> None:
    """A tela do usuario mostrava tres erros para uma causa so.

    Ambiente falhou -> Licenca, Evolution e "Teste final" repetiam a mesma
    causa com outras palavras, escondendo qual deles precisava de acao.
    """
    monkeypatch.chdir(tmp_path)
    configuration = AppConfigurationManager(project_root=tmp_path)

    report = AutomaticSetupService(
        configuration_manager=configuration,
        environment_manager=FailingEnvironmentManager(),
        backend_runtime_manager=FakeBackendRuntimeManager(),
        evolution_provisioning_manager=FakeEvolutionProvisioning(),
        diagnostic_service=FakeDiagnosticService(),
        ffmpeg_manager=FfmpegManager(configuration_manager=configuration, project_root=tmp_path),
        license_service=FakeLicenseService(LicenseStatus.ACTIVE),
    ).prepare()

    failed = [step for step in report.steps if step.status is SetupStepStatus.ERROR]

    assert [step.key for step in failed] == ["environment"]
    waiting = [step for step in report.steps if step.status is SetupStepStatus.PENDING]
    assert {step.key for step in waiting} == {"license", "evolution", "diagnostic"}
    # Cada uma aponta para a etapa que precisa ser resolvida antes.
    assert all(step.message.startswith("Aguardando a etapa ") for step in waiting)


def test_independent_steps_still_run_when_something_else_failed(tmp_path: Path, monkeypatch) -> None:
    """O FFmpeg nao depende do Docker: bloquea-lo seria esconder informacao."""
    monkeypatch.chdir(tmp_path)
    configuration = AppConfigurationManager(project_root=tmp_path)
    ffmpeg = tmp_path / "bin" / "ffmpeg.exe"
    ffmpeg.parent.mkdir()
    ffmpeg.write_text("fake", encoding="utf-8")

    report = AutomaticSetupService(
        configuration_manager=configuration,
        environment_manager=FailingEnvironmentManager(),
        backend_runtime_manager=FakeBackendRuntimeManager(),
        evolution_provisioning_manager=FakeEvolutionProvisioning(),
        diagnostic_service=FakeDiagnosticService(),
        ffmpeg_manager=FfmpegManager(configuration_manager=configuration, project_root=tmp_path),
        license_service=FakeLicenseService(LicenseStatus.ACTIVE),
    ).prepare()

    ffmpeg_step = next(step for step in report.steps if step.key == "ffmpeg")
    assert ffmpeg_step.status is not SetupStepStatus.PENDING


def test_the_report_is_written_to_disk(tmp_path: Path, monkeypatch) -> None:
    """Se a janela fechar, o relatorio precisa continuar existindo: hoje ele so
    existe enquanto a tela estiver aberta."""
    monkeypatch.chdir(tmp_path)
    configuration = AppConfigurationManager(project_root=tmp_path)

    AutomaticSetupService(
        configuration_manager=configuration,
        environment_manager=FakeEnvironmentManager(),
        backend_runtime_manager=FakeBackendRuntimeManager(),
        evolution_provisioning_manager=FakeEvolutionProvisioning(),
        diagnostic_service=FakeDiagnosticService(),
        ffmpeg_manager=FfmpegManager(configuration_manager=configuration, project_root=tmp_path),
        license_service=FakeLicenseService(LicenseStatus.ACTIVE),
        runtime_root=tmp_path / "runtime",
    ).prepare()

    report_file = tmp_path / "runtime" / "logs" / "setup-report.json"
    assert report_file.exists()
    saved = json.loads(report_file.read_text(encoding="utf-8"))
    assert saved["status"] == "OK"
    assert any(step["key"] == "environment" for step in saved["steps"])
    assert "gerado_em" in saved


def test_an_unverifiable_license_blocks_the_steps_that_depend_on_it(tmp_path: Path, monkeypatch) -> None:
    """WARNING tambem bloqueia.

    Com a Evolution fora do ar a licenca fica em WARNING ("nao consegui falar"),
    e provisionar em seguida produzia um segundo vermelho para a mesma causa.
    """
    monkeypatch.chdir(tmp_path)
    # Sem zerar, a espera pela Evolution gira os 120s reais do tempo limite.
    monkeypatch.setattr(AutomaticSetupService, "EVOLUTION_READY_TIMEOUT_SECONDS", 0)
    configuration = AppConfigurationManager(project_root=tmp_path)

    report = AutomaticSetupService(
        configuration_manager=configuration,
        environment_manager=FakeEnvironmentManager(),
        backend_runtime_manager=FakeBackendRuntimeManager(),
        evolution_provisioning_manager=FakeEvolutionProvisioning(),
        diagnostic_service=FakeDiagnosticService(),
        ffmpeg_manager=FfmpegManager(configuration_manager=configuration, project_root=tmp_path),
        license_service=FakeLicenseService(LicenseStatus.UNAVAILABLE),
    ).prepare()

    license_step = next(step for step in report.steps if step.key == "license")
    assert license_step.status is SetupStepStatus.WARNING

    evolution_step = next(step for step in report.steps if step.key == "evolution")
    assert evolution_step.status is SetupStepStatus.PENDING
    # E o teste final nao repete a mesma causa como um terceiro vermelho.
    diagnostic = next(step for step in report.steps if step.key == "diagnostic")
    assert diagnostic.status is SetupStepStatus.PENDING


def test_progress_is_published_while_the_steps_run(tmp_path: Path, monkeypatch) -> None:
    """A tela precisa ver a etapa atual, nao um spinner mudo por minutos."""
    from app.services.setup_progress import SetupProgressStore

    monkeypatch.chdir(tmp_path)
    configuration = AppConfigurationManager(project_root=tmp_path)
    progress = SetupProgressStore()
    seen: list[tuple[str, SetupStepStatus]] = []

    class SpyEnvironment(FakeEnvironmentManager):
        def prepare(self, install_docker: bool = True):
            # Durante a etapa Ambiente, o instantaneo ja deve mostra-la correndo.
            snapshot = progress.snapshot()
            step = next(s for s in snapshot.steps if s.key == "environment")
            seen.append((step.key, step.status))
            return super().prepare(install_docker)

    AutomaticSetupService(
        configuration_manager=configuration,
        environment_manager=SpyEnvironment(),
        backend_runtime_manager=FakeBackendRuntimeManager(),
        evolution_provisioning_manager=FakeEvolutionProvisioning(),
        diagnostic_service=FakeDiagnosticService(),
        ffmpeg_manager=FfmpegManager(configuration_manager=configuration, project_root=tmp_path),
        license_service=FakeLicenseService(LicenseStatus.ACTIVE),
        progress_store=progress,
    ).prepare()

    assert seen == [("environment", SetupStepStatus.RUNNING)]
    assert progress.is_running() is False
    assert progress.snapshot().status is SetupStepStatus.OK


def test_a_second_prepare_does_not_run_in_parallel(tmp_path: Path, monkeypatch) -> None:
    """Clicar duas vezes disparava dois `docker compose up` competindo pelos
    mesmos containers."""
    from app.services.setup_progress import SetupProgressStore

    monkeypatch.chdir(tmp_path)
    configuration = AppConfigurationManager(project_root=tmp_path)
    progress = SetupProgressStore()
    runs = {"count": 0}

    class CountingEnvironment(FakeEnvironmentManager):
        def prepare(self, install_docker: bool = True):
            runs["count"] += 1
            return super().prepare(install_docker)

    service = AutomaticSetupService(
        configuration_manager=configuration,
        environment_manager=CountingEnvironment(),
        backend_runtime_manager=FakeBackendRuntimeManager(),
        evolution_provisioning_manager=FakeEvolutionProvisioning(),
        diagnostic_service=FakeDiagnosticService(),
        ffmpeg_manager=FfmpegManager(configuration_manager=configuration, project_root=tmp_path),
        license_service=FakeLicenseService(LicenseStatus.ACTIVE),
        progress_store=progress,
    )

    # Simula um preparo em andamento quando o segundo clique chega.
    progress.start([("config", "Configuracao")])
    report = service.prepare()

    assert runs["count"] == 0, "o segundo preparo nao pode rodar em paralelo"
    assert report.status is SetupStepStatus.RUNNING
