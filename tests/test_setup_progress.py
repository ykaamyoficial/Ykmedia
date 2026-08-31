"""O preparo leva minutos e a tela ficava muda o tempo todo.

Sem sinal de progresso o usuario nao sabe se travou, e clicar de novo disparava
um segundo preparo em paralelo -- dois `docker compose up` competindo pelos
mesmos containers.
"""

import threading
import time

from app.services.setup_progress import SetupProgressStore
from app.services.configuration_manager import SetupStepResult, SetupStepStatus


def _result(key: str, status: SetupStepStatus = SetupStepStatus.OK) -> SetupStepResult:
    return SetupStepResult(key, key.title(), status, "pronto")


def test_snapshot_is_empty_before_anything_runs() -> None:
    store = SetupProgressStore()

    assert store.snapshot() is None
    assert store.is_running() is False


def test_steps_appear_as_they_run() -> None:
    store = SetupProgressStore()
    store.start([("config", "Configuracao"), ("environment", "Ambiente")])

    store.mark_running("config")
    snapshot = store.snapshot()
    assert snapshot is not None
    statuses = {step.key: step.status for step in snapshot.steps}
    assert statuses["config"] is SetupStepStatus.RUNNING
    # A etapa que ainda nao comecou ja aparece, para o usuario ver o caminho
    # inteiro em vez de uma lista que cresce do nada.
    assert statuses["environment"] is SetupStepStatus.PENDING

    store.record(_result("config"))
    assert store.snapshot().steps[0].status is SetupStepStatus.OK


def test_running_flag_reflects_the_lifecycle() -> None:
    store = SetupProgressStore()
    assert store.is_running() is False

    store.start([("config", "Configuracao")])
    assert store.is_running() is True

    store.finish(message="Sistema pronto.", status=SetupStepStatus.OK)
    assert store.is_running() is False
    assert store.snapshot().message == "Sistema pronto."


def test_concurrent_readers_never_see_a_half_written_report() -> None:
    """A tela consulta o progresso enquanto o preparo escreve nele."""
    store = SetupProgressStore()
    store.start([(f"s{i}", f"Etapa {i}") for i in range(20)])
    errors: list[Exception] = []

    def writer() -> None:
        try:
            for i in range(20):
                store.mark_running(f"s{i}")
                store.record(_result(f"s{i}"))
                time.sleep(0.001)
        except Exception as exc:  # noqa: BLE001
            errors.append(exc)

    def reader() -> None:
        try:
            for _ in range(200):
                snapshot = store.snapshot()
                assert snapshot is not None
                assert len(snapshot.steps) == 20
        except Exception as exc:  # noqa: BLE001
            errors.append(exc)

    threads = [threading.Thread(target=writer), threading.Thread(target=reader)]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()

    assert errors == []
