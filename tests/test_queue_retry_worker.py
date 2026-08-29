import asyncio
from datetime import datetime, timedelta, timezone

from app.services.processing_queue import (
    ProcessingJobOrigin,
    ProcessingJobStatus,
    ProcessingQueue,
)
from app.services.queue_retry_worker import QueueRetryWorker


class FakeReprocessor:
    def __init__(self, outcomes: list[tuple[list[str], bool] | Exception]) -> None:
        self._outcomes = list(outcomes)
        self.calls: list[dict] = []

    async def reprocess(self, payload: dict[str, object]) -> tuple[list[str], bool]:
        self.calls.append(payload)
        outcome = self._outcomes.pop(0) if self._outcomes else ([], True)
        if isinstance(outcome, Exception):
            raise outcome
        return outcome


def _due_retry_job(queue: ProcessingQueue) -> object:
    job = queue.enqueue("s", ProcessingJobOrigin.WHATSAPP, {"i": 1})
    queue.dequeue()
    queue.schedule_retry(job, "download: falha")
    job.next_attempt_at = datetime.now(timezone.utc) - timedelta(seconds=1)
    return job


def test_drain_once_completes_a_job_that_now_succeeds() -> None:
    queue = ProcessingQueue()
    job = _due_retry_job(queue)
    worker = QueueRetryWorker(queue, FakeReprocessor([([], True)]))

    drained = asyncio.run(worker.drain_once())

    assert drained == 1
    assert job.status is ProcessingJobStatus.COMPLETED


def test_drain_once_reschedules_a_job_that_still_fails() -> None:
    queue = ProcessingQueue()
    job = _due_retry_job(queue)
    worker = QueueRetryWorker(queue, FakeReprocessor([(["download: ainda falha"], True)]))

    asyncio.run(worker.drain_once())

    assert job.status is ProcessingJobStatus.RETRYING
    assert job.attempts == 2


def test_drain_once_reschedules_when_reprocessor_raises() -> None:
    queue = ProcessingQueue()
    job = _due_retry_job(queue)
    worker = QueueRetryWorker(queue, FakeReprocessor([RuntimeError("boom")]))

    asyncio.run(worker.drain_once())

    assert job.status is ProcessingJobStatus.RETRYING


def test_drain_once_dead_letters_after_max_attempts() -> None:
    queue = ProcessingQueue()
    job = queue.enqueue("s", ProcessingJobOrigin.WHATSAPP, {"i": 1})
    queue.dequeue()
    for _ in range(ProcessingQueue.MAX_ATTEMPTS - 1):
        queue.schedule_retry(job, "download: falha")
    job.next_attempt_at = datetime.now(timezone.utc) - timedelta(seconds=1)
    worker = QueueRetryWorker(queue, FakeReprocessor([(["download: falha"], True)]))

    asyncio.run(worker.drain_once())

    assert job.status is ProcessingJobStatus.DEAD_LETTER


def test_start_and_stop_are_idempotent() -> None:
    async def scenario() -> None:
        queue = ProcessingQueue()
        worker = QueueRetryWorker(queue, FakeReprocessor([]), idle_interval=0.05)
        worker.start()
        worker.start()
        await asyncio.sleep(0.12)
        await worker.stop()
        await worker.stop()

    asyncio.run(scenario())
