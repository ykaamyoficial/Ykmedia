import time
import sys

from app.services.backend_runtime_manager import (
    BackendRuntimeEvent,
    BackendRuntimeManager,
    BackendRuntimeState,
)


class FakeProcess:
    def __init__(self) -> None:
        self.terminated = False
        self.killed = False
        self.return_code: int | None = None

    def poll(self) -> int | None:
        return self.return_code

    def terminate(self) -> None:
        self.terminated = True
        self.return_code = 0

    def wait(self, timeout: float | None = None) -> int:
        return self.return_code or 0

    def kill(self) -> None:
        self.killed = True
        self.return_code = -9


def _wait_until(predicate, timeout: float = 1.0) -> None:
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if predicate():
            return
        time.sleep(0.01)
    raise AssertionError("condicao nao atendida dentro do tempo esperado")


def test_reuses_existing_backend_when_health_is_online() -> None:
    started_processes: list[FakeProcess] = []
    manager = BackendRuntimeManager(
        health_checker=lambda url, timeout: True,
        process_starter=lambda: started_processes.append(FakeProcess()) or started_processes[-1],
        monitor_interval_seconds=0.01,
    )

    snapshot = manager.start()

    assert snapshot.state is BackendRuntimeState.ONLINE
    assert snapshot.managed_process is False
    assert started_processes == []

    manager.stop()


def test_starts_backend_when_health_is_offline() -> None:
    process = FakeProcess()
    manager = BackendRuntimeManager(
        health_checker=lambda url, timeout: False,
        process_starter=lambda: process,
        monitor_interval_seconds=0.01,
    )

    snapshot = manager.start()

    assert snapshot.state is BackendRuntimeState.STARTING
    assert snapshot.managed_process is True

    manager.stop()
    assert process.terminated is True


def test_does_not_stop_external_backend() -> None:
    manager = BackendRuntimeManager(
        health_checker=lambda url, timeout: True,
        process_starter=lambda: FakeProcess(),
        monitor_interval_seconds=0.01,
    )

    manager.start()
    snapshot = manager.stop()

    assert snapshot.state is BackendRuntimeState.STOPPED
    assert snapshot.managed_process is False


def test_restarts_managed_backend_after_unexpected_exit() -> None:
    health_checks = iter([False, False, False, True])
    processes = [FakeProcess(), FakeProcess()]

    def health_checker(url: str, timeout: float) -> bool:
        return next(health_checks, True)

    manager = BackendRuntimeManager(
        health_checker=health_checker,
        process_starter=lambda: processes.pop(0),
        monitor_interval_seconds=0.01,
        restart_attempts=3,
    )
    manager.start()
    first_process = manager._process
    assert isinstance(first_process, FakeProcess)

    first_process.return_code = 1

    _wait_until(lambda: manager.snapshot().restart_attempts == 1)

    assert manager.snapshot().managed_process is True
    assert manager.snapshot().restart_attempts == 1

    manager.stop()


def test_stops_restart_loop_after_attempt_limit() -> None:
    processes = [FakeProcess(), FakeProcess()]
    manager = BackendRuntimeManager(
        health_checker=lambda url, timeout: False,
        process_starter=lambda: processes.pop(0),
        monitor_interval_seconds=0.01,
        restart_attempts=1,
    )
    events: list[BackendRuntimeEvent] = []
    manager.on_event(lambda event, snapshot: events.append(event))
    manager.start()
    first_process = manager._process
    assert isinstance(first_process, FakeProcess)
    first_process.return_code = 1

    _wait_until(lambda: manager.snapshot().restart_attempts == 1)
    second_process = manager._process
    assert isinstance(second_process, FakeProcess)
    second_process.return_code = 1

    _wait_until(lambda: manager.snapshot().state is BackendRuntimeState.ERROR)

    assert manager.snapshot().last_error == "Limite de tentativas de reinicio atingido."
    assert BackendRuntimeEvent.ERROR in events

    manager.stop()


def test_backend_command_uses_current_python_in_development() -> None:
    manager = BackendRuntimeManager(host="0.0.0.0", port=8010)

    command = manager._backend_command()

    assert command == [
        sys.executable,
        "-m",
        "uvicorn",
        "app.main:app",
        "--host",
        "0.0.0.0",
        "--port",
        "8010",
    ]


def test_backend_command_uses_executable_backend_mode_when_frozen(monkeypatch) -> None:
    monkeypatch.setattr(sys, "frozen", True, raising=False)
    monkeypatch.setattr(sys, "executable", "YkMedia.exe")
    manager = BackendRuntimeManager()

    assert manager._backend_command() == ["YkMedia.exe", "--backend"]
