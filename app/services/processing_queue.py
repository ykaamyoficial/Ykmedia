import logging
from collections import deque
from collections.abc import Awaitable, Callable
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import StrEnum
from threading import RLock
from typing import Any
from uuid import uuid4

from app.services.storage_service import StorageService

logger = logging.getLogger(__name__)


class ProcessingJobStatus(StrEnum):
    PENDING = "PENDENTE"
    PROCESSING = "PROCESSANDO"
    COMPLETED = "CONCLUIDO"
    ERROR = "ERRO"


class ProcessingJobOrigin(StrEnum):
    WHATSAPP = "WhatsApp"
    YOUTUBE = "YouTube"


@dataclass(slots=True)
class ProcessingJob:
    id: str
    sender: str
    origin: ProcessingJobOrigin
    created_at: datetime
    status: ProcessingJobStatus
    payload: dict[str, Any] = field(repr=False)
    result: Any | None = None
    error: str | None = None


class ProcessingQueue:
    def __init__(self, storage_service: StorageService | None = None) -> None:
        self._storage_service = storage_service
        self._pending: deque[ProcessingJob] = deque()
        self._history: dict[str, ProcessingJob] = {}
        self._lock = RLock()
        self._restore_jobs()

    def enqueue(
        self,
        sender: str,
        origin: ProcessingJobOrigin,
        payload: dict[str, Any],
    ) -> ProcessingJob:
        job = ProcessingJob(
            id=str(uuid4()),
            sender=sender,
            origin=origin,
            created_at=datetime.now(timezone.utc),
            status=ProcessingJobStatus.PENDING,
            payload=payload,
        )

        with self._lock:
            self._pending.append(job)
            self._history[job.id] = job
            self._persist(job)

        logger.info("Job criado: id=%s origem=%s remetente=%s", job.id, job.origin.value, job.sender)
        return job

    def dequeue(self) -> ProcessingJob | None:
        with self._lock:
            if not self._pending:
                return None

            job = self._pending.popleft()
            job.status = ProcessingJobStatus.PROCESSING
            self._persist(job)

        logger.info("Job em processamento: id=%s", job.id)
        return job

    def update(self, job: ProcessingJob) -> None:
        with self._lock:
            self._history[job.id] = job
            self._persist(job)

    def list_jobs(self) -> list[ProcessingJob]:
        with self._lock:
            return list(self._history.values())

    def pending_count(self) -> int:
        with self._lock:
            return len(self._pending)

    def clear_completed(self) -> int:
        with self._lock:
            completed_ids = [
                job_id
                for job_id, job in self._history.items()
                if job.status is ProcessingJobStatus.COMPLETED
            ]

            for job_id in completed_ids:
                self._history.pop(job_id, None)

            if self._storage_service is not None:
                self._storage_service.delete_completed_processing_jobs()

            return len(completed_ids)

    def _restore_jobs(self) -> None:
        if self._storage_service is None:
            return

        for row in self._storage_service.list_processing_jobs():
            job = ProcessingJob(
                id=str(row["id"]),
                sender=str(row["sender"]),
                origin=ProcessingJobOrigin(str(row["origin"])),
                created_at=datetime.fromisoformat(str(row["created_at"])),
                status=ProcessingJobStatus(str(row["status"])),
                payload=dict(row["payload"]),
                error=str(row["error"]) if row.get("error") is not None else None,
            )
            self._history[job.id] = job
            if job.status in {ProcessingJobStatus.PENDING, ProcessingJobStatus.PROCESSING}:
                job.status = ProcessingJobStatus.PENDING
                self._pending.append(job)

    def _persist(self, job: ProcessingJob) -> None:
        if self._storage_service is None:
            return

        self._storage_service.save_processing_job(
            job_id=job.id,
            sender=job.sender,
            origin=job.origin.value,
            created_at=job.created_at.isoformat(),
            status=job.status.value,
            payload=job.payload,
            error=job.error,
        )


class ProcessingWorker:
    async def process_next(
        self,
        queue: ProcessingQueue,
        handler: Callable[[ProcessingJob], Awaitable[Any]],
    ) -> Any | None:
        job = queue.dequeue()
        if job is None:
            return None

        try:
            result = await handler(job)
        except Exception as exc:
            job.status = ProcessingJobStatus.ERROR
            job.error = str(exc)
            queue.update(job)
            logger.error("Job com erro: id=%s motivo=%s", job.id, exc)
            raise

        job.result = result
        job.status = ProcessingJobStatus.COMPLETED
        queue.update(job)
        logger.info("Job finalizado: id=%s", job.id)
        return result
