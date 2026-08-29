import logging
from collections import deque
from collections.abc import Awaitable, Callable
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
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
    RETRYING = "REPROCESSANDO"
    DEAD_LETTER = "FALHA_PERMANENTE"


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
    attempts: int = 0
    next_attempt_at: datetime | None = None


class ProcessingQueue:
    MAX_ATTEMPTS = 5
    RETRY_BASE_SECONDS = 30.0
    RETRY_CAP_SECONDS = 3600.0

    def __init__(self, storage_service: StorageService | None = None) -> None:
        self._storage_service = storage_service
        self._pending: deque[ProcessingJob] = deque()
        self._scheduled: dict[str, ProcessingJob] = {}
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
            self._promote_due_retries()
            if not self._pending:
                return None

            job = self._pending.popleft()
            job.status = ProcessingJobStatus.PROCESSING
            self._persist(job)

        logger.info("Job em processamento: id=%s tentativa=%s", job.id, job.attempts + 1)
        return job

    def update(self, job: ProcessingJob) -> None:
        with self._lock:
            self._history[job.id] = job
            self._persist(job)

    def schedule_retry(self, job: ProcessingJob, error: str) -> bool:
        """Reagenda o job com backoff exponencial. Retorna False se foi para dead-letter."""
        with self._lock:
            job.attempts += 1
            job.error = error
            if job.attempts >= self.MAX_ATTEMPTS:
                job.status = ProcessingJobStatus.DEAD_LETTER
                job.next_attempt_at = None
                self._history[job.id] = job
                self._persist(job)
                logger.error(
                    "Job em dead-letter apos %s tentativas: id=%s motivo=%s",
                    job.attempts,
                    job.id,
                    error,
                )
                return False

            delay = min(
                self.RETRY_BASE_SECONDS * (2 ** (job.attempts - 1)),
                self.RETRY_CAP_SECONDS,
            )
            job.status = ProcessingJobStatus.RETRYING
            job.next_attempt_at = datetime.now(timezone.utc) + timedelta(seconds=delay)
            self._history[job.id] = job
            self._scheduled[job.id] = job
            self._persist(job)
            logger.warning(
                "Job reagendado: id=%s tentativa=%s em %.0fs motivo=%s",
                job.id,
                job.attempts,
                delay,
                error,
            )
            return True

    def mark_completed(self, job: ProcessingJob) -> None:
        with self._lock:
            job.status = ProcessingJobStatus.COMPLETED
            job.next_attempt_at = None
            self._history[job.id] = job
            self._persist(job)

    def claim_due_retries(self) -> list[ProcessingJob]:
        """Move os jobs de retry vencidos para PROCESSING e os devolve."""
        with self._lock:
            self._promote_due_retries()
            claimed: list[ProcessingJob] = []
            while self._pending:
                job = self._pending.popleft()
                job.status = ProcessingJobStatus.PROCESSING
                self._persist(job)
                claimed.append(job)
            return claimed

    def list_jobs(self) -> list[ProcessingJob]:
        with self._lock:
            return list(self._history.values())

    def list_dead_letter(self) -> list[ProcessingJob]:
        with self._lock:
            return [
                job
                for job in self._history.values()
                if job.status is ProcessingJobStatus.DEAD_LETTER
            ]

    def requeue(self, job_id: str) -> bool:
        with self._lock:
            job = self._history.get(job_id)
            if job is None or job.status is not ProcessingJobStatus.DEAD_LETTER:
                return False
            job.status = ProcessingJobStatus.PENDING
            job.attempts = 0
            job.error = None
            job.next_attempt_at = None
            self._pending.append(job)
            self._persist(job)
            return True

    def pending_count(self) -> int:
        with self._lock:
            return len(self._pending) + len(self._scheduled)

    def seconds_until_next_retry(self) -> float | None:
        with self._lock:
            if self._pending:
                return 0.0
            if not self._scheduled:
                return None
            now = datetime.now(timezone.utc)
            waits = [
                (job.next_attempt_at - now).total_seconds()
                for job in self._scheduled.values()
                if job.next_attempt_at is not None
            ]
            if len(waits) != len(self._scheduled):
                return 0.0
            return max(0.0, min(waits))

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

    def _promote_due_retries(self) -> None:
        if not self._scheduled:
            return
        now = datetime.now(timezone.utc)
        due_ids = [
            job_id
            for job_id, job in self._scheduled.items()
            if job.next_attempt_at is None or job.next_attempt_at <= now
        ]
        for job_id in due_ids:
            self._pending.append(self._scheduled.pop(job_id))

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
                attempts=int(row.get("attempts") or 0),
                next_attempt_at=(
                    datetime.fromisoformat(str(row["next_attempt_at"]))
                    if row.get("next_attempt_at") is not None
                    else None
                ),
            )
            self._history[job.id] = job
            if job.status in {ProcessingJobStatus.PENDING, ProcessingJobStatus.PROCESSING}:
                job.status = ProcessingJobStatus.PENDING
                job.next_attempt_at = None
                self._pending.append(job)
            elif job.status is ProcessingJobStatus.RETRYING:
                self._scheduled[job.id] = job

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
            attempts=job.attempts,
            next_attempt_at=(
                job.next_attempt_at.isoformat() if job.next_attempt_at is not None else None
            ),
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
