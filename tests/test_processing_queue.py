import asyncio

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
