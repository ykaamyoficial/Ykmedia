"""Worker de fundo que reprocessa jobs da fila que falharam por causas
transitorias (download da Evolution fora do ar, YouTube instavel, disco cheio).

O webhook continua sincrono: ao receber uma mensagem ele processa na hora e, se
houver erro transitorio, agenda um retry com backoff exponencial. Este worker
acorda periodicamente, pega os retries vencidos e tenta de novo. Apos
`ProcessingQueue.MAX_ATTEMPTS` o job vai para dead-letter (visivel em Downloads).
"""

import asyncio
import logging
from typing import Protocol

from app.services.message_response_sender import MessageResponseSender
from app.services.processing_queue import ProcessingJob, ProcessingQueue
from app.services.receive_media_use_case import ReceiveMediaUseCase

logger = logging.getLogger(__name__)


class JobReprocessor(Protocol):
    async def reprocess(self, payload: dict[str, object]) -> tuple[list[str], bool]:
        """Reprocessa o payload. Retorna (erros_transitorios, entrega_ok)."""
        ...


class WebhookJobReprocessor:
    def __init__(
        self,
        use_case: ReceiveMediaUseCase,
        response_sender: MessageResponseSender,
    ) -> None:
        self._use_case = use_case
        self._response_sender = response_sender

    async def reprocess(self, payload: dict[str, object]) -> tuple[list[str], bool]:
        result = await self._use_case.execute(payload, enqueue=False)
        delivery = await self._response_sender.send_use_case_response(result)
        retryable = [
            error
            for error in result.errors
            if error.startswith(("download:", "youtube:", "storage:"))
        ]
        return retryable, delivery.error is None


class QueueRetryWorker:
    def __init__(
        self,
        queue: ProcessingQueue,
        reprocessor: JobReprocessor,
        idle_interval: float = 20.0,
    ) -> None:
        self._queue = queue
        self._reprocessor = reprocessor
        self._idle_interval = idle_interval
        self._task: asyncio.Task[None] | None = None
        self._stopped = asyncio.Event()

    def start(self) -> None:
        if self._task is not None and not self._task.done():
            return
        self._stopped.clear()
        self._task = asyncio.create_task(self._run(), name="queue-retry-worker")
        logger.info("Worker de retry da fila iniciado.")

    async def stop(self) -> None:
        self._stopped.set()
        if self._task is None:
            return
        self._task.cancel()
        try:
            await self._task
        except asyncio.CancelledError:
            pass
        self._task = None
        logger.info("Worker de retry da fila parado.")

    async def drain_once(self) -> int:
        claimed = self._queue.claim_due_retries()
        for job in claimed:
            await self._process(job)
        return len(claimed)

    async def _run(self) -> None:
        while not self._stopped.is_set():
            try:
                await self.drain_once()
            except Exception:
                logger.exception("Falha no ciclo do worker de retry")

            wait = self._queue.seconds_until_next_retry()
            delay = self._idle_interval if wait is None else min(max(wait, 1.0), self._idle_interval)
            try:
                await asyncio.wait_for(self._stopped.wait(), timeout=delay)
            except asyncio.TimeoutError:
                continue

    async def _process(self, job: ProcessingJob) -> None:
        try:
            retryable_errors, delivered = await self._reprocessor.reprocess(job.payload)
        except Exception as exc:  # noqa: BLE001 - falha inesperada tambem e reagendada
            self._queue.schedule_retry(job, f"reprocesso: {exc}")
            return

        if retryable_errors or not delivered:
            self._queue.schedule_retry(job, "; ".join(retryable_errors) or "entrega_falhou")
        else:
            self._queue.mark_completed(job)
