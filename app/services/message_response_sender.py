from dataclasses import dataclass

from app.services.evolution_client import EvolutionClient, EvolutionClientError
from app.services.receive_media_use_case import ReceiveMediaResult


@dataclass(frozen=True, slots=True)
class MessageDeliveryResult:
    sent: bool
    error: str | None = None


class MessageResponseSender:
    def __init__(self, evolution_client: EvolutionClient) -> None:
        self._evolution_client = evolution_client

    async def send_use_case_response(
        self,
        result: ReceiveMediaResult,
    ) -> MessageDeliveryResult:
        if result.received_message is None or not result.next_message:
            return MessageDeliveryResult(sent=False)

        try:
            await self._evolution_client.send_text_message(
                recipient=result.received_message.sender.remote_jid,
                text=result.next_message,
            )
        except EvolutionClientError as exc:
            return MessageDeliveryResult(sent=False, error=str(exc))

        return MessageDeliveryResult(sent=True)
