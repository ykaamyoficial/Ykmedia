from pathlib import Path

from app.services.backend_runtime_manager import BackendRuntimeSnapshot, BackendRuntimeState
from app.services.diagnostic_service import DiagnosticService, DiagnosticStatus
from app.services.environment_manager import EnvironmentCheck, EnvironmentStatus
from app.services.system_startup_coordinator import StartupReport, StartupStatus, StartupStep, StartupStepStatus


class FakeEnvironmentManager:
    def __init__(self, status: EnvironmentStatus = EnvironmentStatus.READY) -> None:
        self.status = status
        self.prepare_calls = 0

    def check(self) -> EnvironmentCheck:
        return EnvironmentCheck(
            status=self.status,
            docker_installed=self.status is not EnvironmentStatus.DOCKER_MISSING,
            docker_running=self.status not in {EnvironmentStatus.DOCKER_MISSING, EnvironmentStatus.DOCKER_STOPPED},
            compose_available=True,
            containers_running=self.status is EnvironmentStatus.READY,
            message="ambiente pronto" if self.status is EnvironmentStatus.READY else "ambiente com erro",
        )

    def prepare(self, install_docker: bool = True) -> EnvironmentCheck:
        self.prepare_calls += 1
        self.status = EnvironmentStatus.READY
        return self.check()


class FakeBackendRuntimeManager:
    def __init__(self, state: BackendRuntimeState = BackendRuntimeState.ONLINE) -> None:
        self.state = state
        self.restart_calls = 0
        self.start_calls = 0

    def snapshot(self) -> BackendRuntimeSnapshot:
        return BackendRuntimeSnapshot(
            state=self.state,
            health_url="http://localhost:8010/health",
            managed_process=True,
            restart_attempts=0,
            last_error="backend falhou" if self.state is BackendRuntimeState.ERROR else None,
        )

    def start(self) -> BackendRuntimeSnapshot:
        self.start_calls += 1
        self.state = BackendRuntimeState.ONLINE
        return self.snapshot()

    def restart(self) -> BackendRuntimeSnapshot:
        self.restart_calls += 1
        self.state = BackendRuntimeState.ONLINE
        return self.snapshot()


class FakeStartupCoordinator:
    def __init__(self, status: StartupStatus = StartupStatus.READY) -> None:
        self.status = status
        self.prepare_calls = 0

    def check(self) -> StartupReport:
        return StartupReport(
            status=self.status,
            steps=[StartupStep("Webhook", StartupStepStatus.OK, "ok")],
            is_ready=self.status is StartupStatus.READY,
            message="startup pronto" if self.status is StartupStatus.READY else "startup com alerta",
        )

    def prepare(self) -> StartupReport:
        self.prepare_calls += 1
        self.status = StartupStatus.READY
        return self.check()


class FakeEvolutionClient:
    def __init__(self, state: str = "open") -> None:
        self.state = state

    async def get_connection_state(self) -> dict[str, object]:
        return {"instance": {"state": self.state}}


def _service(
    tmp_path: Path,
    environment_status: EnvironmentStatus = EnvironmentStatus.READY,
    backend_state: BackendRuntimeState = BackendRuntimeState.ONLINE,
    startup_status: StartupStatus = StartupStatus.READY,
    whatsapp_state: str = "open",
    ffmpeg_path: str | None = None,
) -> DiagnosticService:
    ffmpeg = tmp_path / "ffmpeg.exe"
    if ffmpeg_path is None:
        ffmpeg.write_text("fake", encoding="utf-8")
        ffmpeg_path = str(ffmpeg)

    return DiagnosticService(
        environment_manager=FakeEnvironmentManager(environment_status),
        backend_runtime_manager=FakeBackendRuntimeManager(backend_state),
        startup_coordinator=FakeStartupCoordinator(startup_status),
        evolution_client=FakeEvolutionClient(whatsapp_state),
        media_root=tmp_path / "media",
        sqlite_database=tmp_path / "ykmedia.sqlite3",
        ffmpeg_path=ffmpeg_path,
    )


def test_diagnostic_report_ok_when_all_components_are_ready(tmp_path: Path) -> None:
    report = _service(tmp_path).run()

    assert report.status is DiagnosticStatus.OK
    assert len(report.items) == 8


def test_diagnostic_warns_when_ffmpeg_is_not_configured(tmp_path: Path) -> None:
    report = _service(tmp_path, ffmpeg_path="").run()

    assert report.status is DiagnosticStatus.WARNING
    assert any(item.key == "ffmpeg" and item.status is DiagnosticStatus.WARNING for item in report.items)


def test_diagnostic_reports_backend_error(tmp_path: Path) -> None:
    report = _service(tmp_path, backend_state=BackendRuntimeState.ERROR).run()

    assert report.status is DiagnosticStatus.ERROR
    assert any(item.key == "backend" and item.status is DiagnosticStatus.ERROR for item in report.items)


def test_diagnostic_auto_fix_prepares_environment_and_backend(tmp_path: Path) -> None:
    environment = FakeEnvironmentManager(EnvironmentStatus.DOCKER_STOPPED)
    backend = FakeBackendRuntimeManager(BackendRuntimeState.OFFLINE)
    startup = FakeStartupCoordinator(StartupStatus.BACKEND_ERROR)
    service = DiagnosticService(
        environment_manager=environment,
        backend_runtime_manager=backend,
        startup_coordinator=startup,
        evolution_client=FakeEvolutionClient(),
        media_root=tmp_path / "media",
        sqlite_database=tmp_path / "ykmedia.sqlite3",
        ffmpeg_path="",
    )

    report = service.auto_fix()

    assert environment.prepare_calls == 1
    assert backend.start_calls == 1
    assert startup.prepare_calls == 1
    assert report.status is DiagnosticStatus.WARNING


def test_diagnostic_restart_backend_uses_runtime_manager(tmp_path: Path) -> None:
    backend = FakeBackendRuntimeManager(BackendRuntimeState.ERROR)
    service = DiagnosticService(
        environment_manager=FakeEnvironmentManager(),
        backend_runtime_manager=backend,
        startup_coordinator=FakeStartupCoordinator(),
        evolution_client=FakeEvolutionClient(),
        media_root=tmp_path / "media",
        sqlite_database=tmp_path / "ykmedia.sqlite3",
        ffmpeg_path="",
    )

    service.restart_backend()

    assert backend.restart_calls == 1
