"""Guarda o andamento do preparo para a tela poder acompanhar.

O preparo leva minutos (na primeira vez baixa mais de 1 GB) e a interface ficava
muda o tempo todo: o usuario nao sabia se estava trabalhando ou travado, e
clicar de novo disparava um segundo preparo em paralelo -- dois `docker compose
up` competindo pelos mesmos containers.
"""

import threading

from app.services.configuration_manager import SetupReport, SetupStepResult, SetupStepStatus


class SetupProgressStore:
    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._steps: dict[str, SetupStepResult] = {}
        self._order: list[str] = []
        self._running = False
        self._message = ""
        self._status = SetupStepStatus.PENDING
        self._started = False

    def start(self, steps: list[tuple[str, str]]) -> None:
        """Publica o caminho inteiro de uma vez.

        Mostrar todas as etapas desde o inicio deixa claro o que ainda vem, em
        vez de uma lista que cresce do nada enquanto o usuario espera.
        """
        with self._lock:
            self._order = [key for key, _ in steps]
            self._steps = {
                key: SetupStepResult(key, label, SetupStepStatus.PENDING, "Aguardando a vez.")
                for key, label in steps
            }
            self._running = True
            self._started = True
            self._status = SetupStepStatus.RUNNING
            self._message = "Preparando o sistema..."

    def mark_running(self, key: str) -> None:
        with self._lock:
            current = self._steps.get(key)
            if current is None:
                return
            self._steps[key] = SetupStepResult(
                current.key, current.label, SetupStepStatus.RUNNING, "Em andamento..."
            )

    def record(self, result: SetupStepResult) -> None:
        with self._lock:
            if result.key not in self._steps:
                self._order.append(result.key)
            self._steps[result.key] = result

    def finish(self, message: str, status: SetupStepStatus) -> None:
        with self._lock:
            self._running = False
            self._message = message
            self._status = status

    def is_running(self) -> bool:
        with self._lock:
            return self._running

    def snapshot(self) -> SetupReport | None:
        with self._lock:
            if not self._started:
                return None
            steps = [self._steps[key] for key in self._order if key in self._steps]
            return SetupReport(status=self._status, steps=steps, message=self._message)
