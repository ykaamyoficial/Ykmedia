from app.services.backend_runtime_manager import BackendRuntimeSnapshot, BackendRuntimeState
from app.services.environment_manager import EnvironmentCheck, EnvironmentStatus
from app.services.system_startup_coordinator import StartupStatus, SystemStartupCoordinator


class FakeEnvironmentManager:
    def __init__(self, check_result: EnvironmentCheck) -> None:
        self.check_result = check_result
        self.prepare_calls = 0

    def check(self) -> EnvironmentCheck:
        return self.check_result

    def prepare(self, install_docker: bool = True) -> EnvironmentCheck:
        self.prepare_calls += 1
        return self.check_result


class FakeBackendRuntimeManager:
    def __init__(self, state: BackendRuntimeState = BackendRuntimeState.ONLINE) -> None:
        self.snapshot_result = BackendRuntimeSnapshot(
            state=state,
            health_url="http://localhost:8010/health",
            managed_process=True,
            restart_attempts=0,
            last_error="backend falhou" if state is BackendRuntimeState.ERROR else None,
        )
        self.start_calls = 0

    def start(self) -> BackendRuntimeSnapshot:
        self.start_calls += 1
        return self.snapshot_result

    def snapshot(self) -> BackendRuntimeSnapshot:
        return self.snapshot_result


class FakeEvolutionClient:
    def __init__(self, state: str = "open") -> None:
        self.state = state

    async def get_connection_state(self) -> dict[str, object]:
        return {"instance": {"state": self.state}}


def _environment(status: EnvironmentStatus = EnvironmentStatus.READY) -> EnvironmentCheck:
    return EnvironmentCheck(
        status=status,
        docker_installed=status is not EnvironmentStatus.DOCKER_MISSING,
        docker_running=status not in {EnvironmentStatus.DOCKER_MISSING, EnvironmentStatus.DOCKER_STOPPED},
        compose_available=True,
        containers_running=status is EnvironmentStatus.READY,
        message=f"environment {status.value}",
    )


def _coordinator(
    environment_status: EnvironmentStatus = EnvironmentStatus.READY,
    backend_state: BackendRuntimeState = BackendRuntimeState.ONLINE,
    webhook_reachable: bool = True,
    whatsapp_state: str = "open",
) -> SystemStartupCoordinator:
    return SystemStartupCoordinator(
        environment_manager=FakeEnvironmentManager(_environment(environment_status)),
        backend_runtime_manager=FakeBackendRuntimeManager(backend_state),
        evolution_client=FakeEvolutionClient(whatsapp_state),
        webhook_checker=lambda url, secret: webhook_reachable,
    )


def test_prepare_reports_ready_when_all_services_are_available() -> None:
    report = _coordinator().prepare()

    assert report.status is StartupStatus.READY
    assert report.is_ready is True
    assert [step.name for step in report.steps] == [
        "Docker e containers",
        "Backend FastAPI",
        "Webhook",
        "WhatsApp",
    ]


def test_check_reports_missing_docker() -> None:
    report = _coordinator(environment_status=EnvironmentStatus.DOCKER_MISSING).check()

    assert report.status is StartupStatus.DOCKER_MISSING
    assert report.is_ready is False


def test_prepare_reports_backend_error() -> None:
    report = _coordinator(backend_state=BackendRuntimeState.ERROR).prepare()

    assert report.status is StartupStatus.BACKEND_ERROR
    assert report.is_ready is False


def test_prepare_reports_unreachable_webhook() -> None:
    report = _coordinator(webhook_reachable=False).prepare()

    assert report.status is StartupStatus.WEBHOOK_UNREACHABLE
    assert report.is_ready is False


def test_prepare_reports_disconnected_whatsapp() -> None:
    report = _coordinator(whatsapp_state="close").prepare()

    assert report.status is StartupStatus.WHATSAPP_DISCONNECTED
    assert report.is_ready is False
    assert report.steps[-1].name == "WhatsApp"
