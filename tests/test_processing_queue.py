import asyncio
from datetime import datetime, timedelta, timezone

import pytest

from app.services.processing_queue import (
    ProcessingJob,
    ProcessingJobOrigin,
    ProcessingJobStatus,
    ProcessingQueue,
    ProcessingWorker,
)


def test_enqueue_adds_pending_job() -> None:
    queue = ProcessingQueue()

    job = queue.enqueue(
        sender="sender-1",
        origin=ProcessingJobOrigin.WHATSAPP,
        payload={"event": "messages.upsert"},
    )

    assert job.sender == "sender-1"
    assert job.origin is ProcessingJobOrigin.WHATSAPP
    assert job.status is ProcessingJobStatus.PENDING
    assert queue.pending_count() == 1


def test_worker_processes_fifo_order() -> None:
    queue = ProcessingQueue()
    worker = ProcessingWorker()
    queue.enqueue("sender-1", ProcessingJobOrigin.WHATSAPP, {"index": 1})
    queue.enqueue("sender-2", ProcessingJobOrigin.YOUTUBE, {"index": 2})
    processed_indexes: list[int] = []

    async def handler(job: ProcessingJob) -> int:
        processed_indexes.append(int(job.payload["index"]))
        return int(job.payload["index"])

    first_result = asyncio.run(worker.process_next(queue, handler))
    second_result = asyncio.run(worker.process_next(queue, handler))

    assert first_result == 1
    assert second_result == 2
    assert processed_indexes == [1, 2]


def test_error_job_does_not_block_next_job() -> None:
    queue = ProcessingQueue()
    worker = ProcessingWorker()
    queue.enqueue("sender-1", ProcessingJobOrigin.WHATSAPP, {"index": 1})
    queue.enqueue("sender-2", ProcessingJobOrigin.WHATSAPP, {"index": 2})

    async def failing_handler(job: ProcessingJob) -> int:
        raise RuntimeError("falha")

    async def success_handler(job: ProcessingJob) -> int:
        return int(job.payload["index"])

    with pytest.raises(RuntimeError):
        asyncio.run(worker.process_next(queue, failing_handler))

    second_result = asyncio.run(worker.process_next(queue, success_handler))
    jobs = queue.list_jobs()

    assert second_result == 2
    assert jobs[0].status is ProcessingJobStatus.ERROR
    assert jobs[1].status is ProcessingJobStatus.COMPLETED


def test_multiple_consecutive_download_jobs() -> None:
    queue = ProcessingQueue()
    worker = ProcessingWorker()

    for index in range(5):
        queue.enqueue("sender", ProcessingJobOrigin.WHATSAPP, {"index": index})

    async def handler(job: ProcessingJob) -> int:
        return int(job.payload["index"])

    results = [asyncio.run(worker.process_next(queue, handler)) for _ in range(5)]

    assert results == [0, 1, 2, 3, 4]
    assert queue.pending_count() == 0


def test_schedule_retry_uses_backoff_then_dead_letters() -> None:
    queue = ProcessingQueue()
    job = queue.enqueue("s", ProcessingJobOrigin.WHATSAPP, {"i": 1})
    queue.dequeue()

    for expected_attempt in range(1, ProcessingQueue.MAX_ATTEMPTS):
        assert queue.schedule_retry(job, "download: falha") is True
        assert job.status is ProcessingJobStatus.RETRYING
        assert job.attempts == expected_attempt
        assert job.next_attempt_at is not None

    assert queue.schedule_retry(job, "download: falha") is False
    assert job.status is ProcessingJobStatus.DEAD_LETTER
    assert queue.list_dead_letter() == [job]


def test_claim_due_retries_returns_only_due_jobs() -> None:
    queue = ProcessingQueue()
    job = queue.enqueue("s", ProcessingJobOrigin.WHATSAPP, {"i": 1})
    queue.dequeue()
    queue.schedule_retry(job, "download: falha")  # agenda ~30s no futuro

    assert queue.claim_due_retries() == []

    job.next_attempt_at = datetime.now(timezone.utc) - timedelta(seconds=1)
    claimed = queue.claim_due_retries()

    assert claimed == [job]
    assert job.status is ProcessingJobStatus.PROCESSING


def test_requeue_brings_a_dead_letter_job_back() -> None:
    queue = ProcessingQueue()
    job = queue.enqueue("s", ProcessingJobOrigin.WHATSAPP, {"i": 1})
    queue.dequeue()
    for _ in range(ProcessingQueue.MAX_ATTEMPTS):
        queue.schedule_retry(job, "download: falha")
    assert job.status is ProcessingJobStatus.DEAD_LETTER

    assert queue.requeue(job.id) is True
    assert job.status is ProcessingJobStatus.PENDING
    assert job.attempts == 0
    assert queue.dequeue() is job


def test_clear_completed_jobs() -> None:
    queue = ProcessingQueue()
    worker = ProcessingWorker()
    queue.enqueue("sender-1", ProcessingJobOrigin.WHATSAPP, {"index": 1})
    queue.enqueue("sender-2", ProcessingJobOrigin.WHATSAPP, {"index": 2})

    async def handler(job: ProcessingJob) -> int:
        return int(job.payload["index"])

    asyncio.run(worker.process_next(queue, handler))
    asyncio.run(worker.process_next(queue, handler))

    removed_count = queue.clear_completed()

    assert removed_count == 2
    assert queue.list_jobs() == []
