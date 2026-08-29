"""Avisa o cliente antes da conversa expirar por inatividade.

Sem este aviso, a sessao simplesmente sumia depois de 30 min: o cliente
mandava um arquivo, se distraia, e ao voltar recebia "sua conversa expirou".
O notifier acorda a cada minuto, encontra as sessoes que expiram em breve e
ainda nao foram avisadas, e manda um lembrete.
"""

import asyncio
import logging
import time

from app.services.evolution_client import EvolutionClient, EvolutionClientError
from app.services.message_catalog import WhatsAppMessageCatalog
from app.services.storage_service import StorageService

logger = logging.getLogger(__name__)


class SessionExpiryNotifier:
    def __init__(
        self,
        storage_service: StorageService,
        evolution_client: EvolutionClient,
        warning_seconds: float,
        poll_interval: float = 60.0,
    ) -> None:
        self._storage_service = storage_service
        self._evolution_client = evolution_client
        self._warning_seconds = warning_seconds
        self._poll_interval = poll_interval
        self._task: asyncio.Task[None] | None = None
        self._stopped = asyncio.Event()

    def start(self) -> None:
        if self._task is not None and not self._task.done():
            return
        self._stopped.clear()
        self._task = asyncio.create_task(self._run(), name="session-expiry-notifier")
        logger.info("Notificador de expiracao de sessao iniciado.")

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
        logger.info("Notificador de expiracao de sessao parado.")

    async def notify_due(self) -> int:
        now = time.time()
        rows = self._storage_service.list_sessions_pending_expiry_warning(
            now, now + self._warning_seconds
        )
        sent = 0
        for row in rows:
            sender_id = str(row["sender_id"])
            try:
                await self._evolution_client.send_text_message(
                    recipient=sender_id,
                    text=WhatsAppMessageCatalog.expiry_warning(),
                )
            except EvolutionClientError as exc:
                logger.warning("Falha ao avisar expiracao (%s): %s", sender_id, exc)
                continue
            self._storage_service.mark_expiry_warning_sent(sender_id)
            sent += 1
        return sent

    async def _run(self) -> None:
        while not self._stopped.is_set():
            try:
                await self.notify_due()
            except Exception:
                logger.exception("Falha no ciclo do notificador de expiracao")
            try:
                await asyncio.wait_for(self._stopped.wait(), timeout=self._poll_interval)
            except asyncio.TimeoutError:
                continue
