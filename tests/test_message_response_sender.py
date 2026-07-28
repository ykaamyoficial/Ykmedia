import asyncio

from app.models.message import MessageType, ReceivedMessage, Sender
from app.services.conversation_engine import ConversationState
from app.services.message_response_sender import MessageResponseSender
from app.services.receive_media_use_case import ReceiveMediaResult


class FakeEvolutionClient:
    def __init__(self) -> None:
        self.calls: list[tuple[str, str]] = []

    async def send_text_message(self, recipient: str, text: str) -> dict[str, object]:
        self.calls.append((recipient, text))
        return {"status": "PENDING"}


def test_sends_use_case_next_message_to_sender() -> None:
    evolution_client = FakeEvolutionClient()
    sender = MessageResponseSender(evolution_client=evolution_client)  # type: ignore[arg-type]
    result = ReceiveMediaResult(
        received_message=ReceivedMessage(
            message_id="MSG1",
            sender=Sender(remote_jid="556299999999@s.whatsapp.net"),
            message_type=MessageType.IMAGE,
            raw_type="imageMessage",
        ),
        stored_file=None,
        conversation_state=ConversationState.WAITING_CATEGORY,
        next_message="Recebi seu arquivo.",
    )

    delivery = asyncio.run(sender.send_use_case_response(result))

    assert delivery.sent is True
    assert evolution_client.calls == [
        ("556299999999@s.whatsapp.net", "Recebi seu arquivo.")
    ]


def test_does_not_send_when_use_case_has_no_message_to_deliver() -> None:
    evolution_client = FakeEvolutionClient()
    sender = MessageResponseSender(evolution_client=evolution_client)  # type: ignore[arg-type]
    result = ReceiveMediaResult(
        received_message=None,
        stored_file=None,
        conversation_state=None,
        next_message=None,
    )

    delivery = asyncio.run(sender.send_use_case_response(result))

    assert delivery.sent is False
    assert delivery.error is None
    assert evolution_client.calls == []
