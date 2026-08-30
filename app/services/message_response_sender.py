from dataclasses import dataclass
from datetime import datetime, timezone
import logging
from uuid import uuid4

from app.models.interactive import InteractivePrompt
from app.models.persistence import (
    ConversationMessageDirection,
    ConversationMessageRecord,
    ConversationMessageStatus,
)
from app.repositories.conversation_message_repository import ConversationMessageRepository
from app.services.evolution_client import EvolutionClient, EvolutionClientError
from app.services.receive_media_use_case import ReceiveMediaResult

logger = logging.getLogger(__name__)


@dataclass(frozen=True, slots=True)
class MessageDeliveryResult:
    sent: bool
    error: str | None = None


class MessageResponseSender:
    def __init__(
        self,
        evolution_client: EvolutionClient,
        conversation_message_repository: ConversationMessageRepository | None = None,
    ) -> None:
        self._evolution_client = evolution_client
        self._conversation_message_repository = conversation_message_repository

    async def send_use_case_response(
        self,
        result: ReceiveMediaResult,
    ) -> MessageDeliveryResult:
        if result.received_message is None or not result.next_message:
            return MessageDeliveryResult(sent=False)

        try:
            await self._send_response(result)
        except EvolutionClientError as exc:
            self._record_outbound_message(result, ConversationMessageStatus.ERROR, str(exc))
            return MessageDeliveryResult(sent=False, error=str(exc))

        self._record_outbound_message(result, ConversationMessageStatus.SENT)
        return MessageDeliveryResult(sent=True)

    #: O WhatsApp aceita no maximo 3 botoes de resposta rapida. Menus maiores
    #: (categorias) continuam como texto numerado.
    MAX_REPLY_BUTTONS = 3

    async def _send_response(self, result: ReceiveMediaResult) -> None:
        if result.received_message is None or not result.next_message:
            return

        recipient = result.received_message.sender.remote_jid
        prompt = result.interactive_prompt
        if prompt is None or not self._fits_in_buttons(prompt):
            await self._evolution_client.send_text_message(recipient=recipient, text=result.next_message)
            return

        try:
            await self._evolution_client.send_reply_buttons(
                recipient=recipient,
                text=prompt.text,
                options=prompt.options,
                footer=prompt.footer,
            )
        except EvolutionClientError as exc:
            logger.warning(
                "Falha ao enviar botoes. Enviando menu em texto. erro=%s",
                exc,
            )
            await self._evolution_client.send_text_message(
                recipient=recipient,
                text=result.next_message,
            )

    def _fits_in_buttons(self, prompt: InteractivePrompt) -> bool:
        return bool(prompt.options) and len(prompt.options) <= self.MAX_REPLY_BUTTONS

    def _record_outbound_message(
        self,
        result: ReceiveMediaResult,
        status: ConversationMessageStatus,
        error: str | None = None,
    ) -> None:
        if (
            self._conversation_message_repository is None
            or result.received_message is None
            or not result.next_message
        ):
            return

        self._conversation_message_repository.save(
            ConversationMessageRecord(
                id=str(uuid4()),
                message_id=result.received_message.message_id,
                sender=result.received_message.sender.remote_jid,
                direction=ConversationMessageDirection.OUTBOUND,
                content=result.next_message,
                message_type="texto",
                state=(
                    result.conversation_state.value
                    if result.conversation_state is not None
                    else None
                ),
                media_id=None,
                created_at=datetime.now(timezone.utc).isoformat(timespec="microseconds"),
                status=status,
                error=error,
            )
        )
