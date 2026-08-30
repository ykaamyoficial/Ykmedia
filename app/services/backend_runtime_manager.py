import logging
import os
import subprocess
import sys
import threading
import time
from collections.abc import Callable
from dataclasses import dataclass
from enum import StrEnum
from typing import Protocol
from urllib.error import URLError
from urllib.request import urlopen

from app.core.config import settings

logger = logging.getLogger(__name__)


class BackendRuntimeState(StrEnum):
    STOPPED = "STOPPED"
    STARTING = "STARTING"
    ONLINE = "ONLINE"
    OFFLINE = "OFFLINE"
    ERROR = "ERROR"


class BackendRuntimeEvent(StrEnum):
    STARTED = "backend_started"
    STOPPED = "backend_stopped"
    ONLINE = "backend_online"
    OFFLINE = "backend_offline"
    ERROR = "backend_error"


class BackendProcess(Protocol):
    def poll(self) -> int | None:
        pass

    def terminate(self) -> None:
        pass

    def wait(self, timeout: float | None = None) -> int:
        pass

    def kill(self) -> None:
        pass


@dataclass(frozen=True, slots=True)
class BackendRuntimeSnapshot:
    state: BackendRuntimeState
    health_url: str
    managed_process: bool
    restart_attempts: int
    last_error: str | None = None


EventCallback = Callable[[BackendRuntimeEvent, BackendRuntimeSnapshot], None]
HealthChecker = Callable[[str, float], bool]
ProcessStarter = Callable[[], BackendProcess]


class BackendRuntimeManager:
    def __init__(
        self,
        host: str | None = None,
        port: int | None = None,
        health_url: str | None = None,
        monitor_interval_seconds: float | None = None,
        startup_timeout_seconds: float | None = None,
        restart_attempts: int | None = None,
        health_checker: HealthChecker | None = None,
        process_starter: ProcessStarter | None = None,
        sleep: Callable[[float], None] = time.sleep,
    ) -> None:
        self.host = host or settings.BACKEND_HOST
        self.port = port if port is not None else settings.BACKEND_PORT
        self.health_url = health_url or settings.BACKEND_HEALTH_URL
        self.monitor_interval_seconds = (
            monitor_interval_seconds
            if monitor_interval_seconds is not None
            else settings.BACKEND_MONITOR_INTERVAL_SECONDS
        )
        self.startup_timeout_seconds = (
            startup_timeout_seconds
            if startup_timeout_seconds is not None
            else settings.BACKEND_STARTUP_TIMEOUT_SECONDS
        )
        self.max_restart_attempts = (
            restart_attempts
            if restart_attempts is not None
            else settings.BACKEND_RESTART_ATTEMPTS
        )
        self._health_checker = health_checker or self._default_health_checker
        self._process_starter = process_starter or self._default_process_starter
        self._sleep = sleep
        self._callbacks: list[EventCallback] = []
        self._lock = threading.RLock()
        self._stop_event = threading.Event()
        self._monitor_thread: threading.Thread | None = None
        self._process: BackendProcess | None = None
        self._managed_process = False
        self._state = BackendRuntimeState.STOPPED
        self._restart_attempts = 0
        self._last_error: str | None = None
        self._startup_deadline: float | None = None

    def start(self) -> BackendRuntimeSnapshot:
        with self._lock:
            if self._monitor_thread is not None and self._monitor_thread.is_alive():
                return self.snapshot()

            self._stop_event.clear()

            if self._is_healthy():
                self._managed_process = False
                self._process = None
                self._set_state(BackendRuntimeState.ONLINE, BackendRuntimeEvent.ONLINE)
                logger.info("Backend existente detectado em %s.", self.health_url)
            else:
                self._start_managed_process()

            self._monitor_thread = threading.Thread(
                target=self._monitor_loop,
                name="YkMediaBackendRuntimeMonitor",
                daemon=True,
            )
            self._monitor_thread.start()
            return self.snapshot()

    def stop(self) -> BackendRuntimeSnapshot:
        with self._lock:
            self._stop_event.set()
            process = self._process if self._managed_process else None

        if process is not None:
            self._terminate_process(process)

        thread = self._monitor_thread
        if thread is not None and thread.is_alive() and thread is not threading.current_thread():
            thread.join(timeout=2.0)

        with self._lock:
            self._process = None
            self._managed_process = False
            self._set_state(BackendRuntimeState.STOPPED, BackendRuntimeEvent.STOPPED)
            logger.info("BackendRuntimeManager finalizado.")
            return self.snapshot()

    def restart(self) -> BackendRuntimeSnapshot:
        self.stop()
        with self._lock:
            self._restart_attempts = 0
            self._last_error = None
        return self.start()

    def snapshot(self) -> BackendRuntimeSnapshot:
        return BackendRuntimeSnapshot(
            state=self._state,
            health_url=self.health_url,
            managed_process=self._managed_process,
            restart_attempts=self._restart_attempts,
            last_error=self._last_error,
        )

    def is_online(self) -> bool:
        return self._is_healthy()

    def on_event(self, callback: EventCallback) -> None:
        with self._lock:
            self._callbacks.append(callback)

    def _monitor_loop(self) -> None:
        while not self._stop_event.wait(self.monitor_interval_seconds):
            with self._lock:
                process = self._process
                managed = self._managed_process

            healthy = self._is_healthy()
            if healthy:
                with self._lock:
                    self._startup_deadline = None
                    self._set_state(BackendRuntimeState.ONLINE, BackendRuntimeEvent.ONLINE)
                continue

            if managed and process is not None and process.poll() is not None:
                logger.warning("Processo do backend foi encerrado inesperadamente.")
                self._handle_unexpected_exit()
                continue

            with self._lock:
                startup_deadline = self._startup_deadline
                state = self._state

            if (
                managed
                and state is BackendRuntimeState.STARTING
                and startup_deadline is not None
                and time.monotonic() < startup_deadline
            ):
                continue

            with self._lock:
                self._set_state(BackendRuntimeState.OFFLINE, BackendRuntimeEvent.OFFLINE)

    def _handle_unexpected_exit(self) -> None:
        with self._lock:
            if self._restart_attempts >= self.max_restart_attempts:
                self._last_error = "Limite de tentativas de reinicio atingido."
                self._set_state(BackendRuntimeState.ERROR, BackendRuntimeEvent.ERROR)
                logger.error(self._last_error)
                return

            self._restart_attempts += 1
            attempt = self._restart_attempts

        logger.info("Reiniciando backend automaticamente. Tentativa %s/%s.", attempt, self.max_restart_attempts)
        try:
            self._start_managed_process()
        except RuntimeError as exc:
            with self._lock:
                self._last_error = str(exc)
                self._set_state(BackendRuntimeState.ERROR, BackendRuntimeEvent.ERROR)

    def _start_managed_process(self) -> None:
        with self._lock:
            self._set_state(BackendRuntimeState.STARTING, None)

        try:
            process = self._process_starter()
        except OSError as exc:
            message = f"Erro ao iniciar backend: {exc}"
            logger.exception(message)
            with self._lock:
                self._last_error = message
                self._set_state(BackendRuntimeState.ERROR, BackendRuntimeEvent.ERROR)
            raise RuntimeError(message) from exc

        with self._lock:
            self._process = process
            self._managed_process = True
            self._startup_deadline = time.monotonic() + self.startup_timeout_seconds
            self._last_error = None
            self._set_state(BackendRuntimeState.STARTING, BackendRuntimeEvent.STARTED)

        logger.info("Backend iniciado em background na porta %s.", self.port)

    def _default_process_starter(self) -> BackendProcess:
        command = self._backend_command()
        options: dict[str, object] = {
            "stdout": subprocess.DEVNULL,
            "stderr": subprocess.DEVNULL,
        }
        if os.name == "nt":
            # Sem isso o Windows abre uma janela de console preta junto do app.
            options["creationflags"] = subprocess.CREATE_NO_WINDOW

        return subprocess.Popen(command, **options)

    def _backend_command(self) -> list[str]:
        if getattr(sys, "frozen", False):
            return [sys.executable, "--backend"]

        return [
            sys.executable,
            "-m",
            "uvicorn",
            "app.main:app",
            "--host",
            self.host,
            "--port",
            str(self.port),
        ]

    def _terminate_process(self, process: BackendProcess) -> None:
        try:
            process.terminate()
            process.wait(timeout=5.0)
            logger.info("Backend gerenciado encerrado corretamente.")
        except subprocess.TimeoutExpired:
            process.kill()
            process.wait(timeout=5.0)
            logger.warning("Backend gerenciado precisou ser finalizado forcadamente.")
        except OSError as exc:
            logger.warning("Erro ao encerrar backend gerenciado: %s", exc)

    def _is_healthy(self) -> bool:
        try:
            return self._health_checker(self.health_url, min(3.0, self.startup_timeout_seconds))
        except Exception as exc:
            logger.debug("Health check do backend falhou: %s", exc)
            return False

    def _default_health_checker(self, url: str, timeout: float) -> bool:
        try:
            with urlopen(url, timeout=timeout) as response:
                return response.status == 200
        except (OSError, URLError):
            return False

    def _set_state(
        self,
        state: BackendRuntimeState,
        event: BackendRuntimeEvent | None,
    ) -> None:
        if self._state == state and event not in {
            BackendRuntimeEvent.STARTED,
            BackendRuntimeEvent.STOPPED,
            BackendRuntimeEvent.ERROR,
        }:
            return

        self._state = state
        if event is not None:
            self._emit(event)

    def _emit(self, event: BackendRuntimeEvent) -> None:
        snapshot = self.snapshot()
        callbacks = list(self._callbacks)
        for callback in callbacks:
            try:
                callback(event, snapshot)
            except Exception:
                logger.exception("Callback de runtime do backend falhou.")
