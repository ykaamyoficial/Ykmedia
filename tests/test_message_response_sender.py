import asyncio

from app.models.interactive import InteractiveOption, InteractivePrompt
from app.models.message import MessageType, ReceivedMessage, Sender
from app.repositories.conversation_message_repository import InMemoryConversationMessageRepository
from app.services.conversation_engine import ConversationState
from app.services.evolution_client import EvolutionClientError
from app.services.message_response_sender import MessageResponseSender
from app.services.receive_media_use_case import ReceiveMediaResult


class FakeEvolutionClient:
    def __init__(self) -> None:
        self.calls: list[tuple[str, object]] = []

    async def send_text_message(self, recipient: str, text: str) -> dict[str, object]:
        self.calls.append(("text", recipient, text))
        return {"status": "PENDING"}

    async def send_reply_buttons(
        self,
        recipient: str,
        text: str,
        options: list[InteractiveOption],
        footer: str | None = None,
    ) -> dict[str, object]:
        self.calls.append(("buttons", recipient, text, tuple(option.id for option in options), footer))
        return {"status": "PENDING"}

    async def send_selection_list(
        self,
        recipient: str,
        text: str,
        button_text: str,
        options: list[InteractiveOption],
        footer: str | None = None,
    ) -> dict[str, object]:
        self.calls.append(("list", recipient, text, button_text, tuple(option.id for option in options), footer))
        return {"status": "PENDING"}


class FailingEvolutionClient:
    async def send_text_message(self, recipient: str, text: str) -> dict[str, object]:
        raise EvolutionClientError("falha envio")


class FailingInteractiveEvolutionClient(FakeEvolutionClient):
    async def send_selection_list(
        self,
        recipient: str,
        text: str,
        button_text: str,
        options: list[InteractiveOption],
        footer: str | None = None,
    ) -> dict[str, object]:
        raise EvolutionClientError("falha interativo")


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
        conversation_state=ConversationState.WAITING_CATEGORY_SELECTION,
        next_message="Recebi seu arquivo.",
    )

    delivery = asyncio.run(sender.send_use_case_response(result))

    assert delivery.sent is True
    assert evolution_client.calls == [
        ("text", "556299999999@s.whatsapp.net", "Recebi seu arquivo.")
    ]


def test_records_outbound_conversation_message() -> None:
    evolution_client = FakeEvolutionClient()
    repository = InMemoryConversationMessageRepository()
    sender = MessageResponseSender(
        evolution_client=evolution_client,  # type: ignore[arg-type]
        conversation_message_repository=repository,
    )
    result = ReceiveMediaResult(
        received_message=ReceivedMessage(
            message_id="MSG1",
            sender=Sender(remote_jid="556299999999@s.whatsapp.net"),
            message_type=MessageType.IMAGE,
            raw_type="imageMessage",
        ),
        stored_file=None,
        conversation_state=ConversationState.WAITING_CATEGORY_SELECTION,
        next_message="Recebi seu arquivo.",
    )

    delivery = asyncio.run(sender.send_use_case_response(result))
    messages = repository.list_by_sender("556299999999@s.whatsapp.net")

    assert delivery.sent is True
    assert len(messages) == 1
    assert messages[0].direction.value == "OUTBOUND"
    assert messages[0].content == "Recebi seu arquivo."
    assert messages[0].status.value == "ENVIADA"


def test_records_outbound_error_when_delivery_fails() -> None:
    repository = InMemoryConversationMessageRepository()
    sender = MessageResponseSender(
        evolution_client=FailingEvolutionClient(),  # type: ignore[arg-type]
        conversation_message_repository=repository,
    )
    result = ReceiveMediaResult(
        received_message=ReceivedMessage(
            message_id="MSG1",
            sender=Sender(remote_jid="556299999999@s.whatsapp.net"),
            message_type=MessageType.IMAGE,
            raw_type="imageMessage",
        ),
        stored_file=None,
        conversation_state=ConversationState.WAITING_CATEGORY_SELECTION,
        next_message="Recebi seu arquivo.",
    )

    delivery = asyncio.run(sender.send_use_case_response(result))
    messages = repository.list_by_sender("556299999999@s.whatsapp.net")

    assert delivery.sent is False
    assert messages[0].status.value == "ERRO"
    assert messages[0].error == "falha envio"


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


def test_sends_selection_list_when_prompt_has_up_to_three_options() -> None:
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
        conversation_state=ConversationState.WAITING_CATEGORY_SELECTION,
        next_message="Escolha uma opcao.",
        interactive_prompt=InteractivePrompt(
            text="Escolha uma opcao.",
            options=[
                InteractiveOption("filename:keep_original", "Manter nome"),
                InteractiveOption("filename:custom", "Informar nome"),
            ],
            footer="YkMedia",
        ),
    )

    delivery = asyncio.run(sender.send_use_case_response(result))

    assert delivery.sent is True
    assert evolution_client.calls == [
        (
            "list",
            "556299999999@s.whatsapp.net",
            "Escolha uma opcao.",
            "Opcoes",
            ("filename:keep_original", "filename:custom"),
            "YkMedia",
        ),
    ]


def test_sends_selection_list_when_prompt_has_more_than_three_options() -> None:
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
        conversation_state=ConversationState.WAITING_CATEGORY_SELECTION,
        next_message="Escolha uma categoria.",
        interactive_prompt=InteractivePrompt(
            text="Escolha uma categoria.",
            options=[InteractiveOption(f"category:{index}", f"Cat {index}") for index in range(1, 5)],
            footer="YkMedia",
            button_text="Ver categorias",
        ),
    )

    delivery = asyncio.run(sender.send_use_case_response(result))

    assert delivery.sent is True
    assert evolution_client.calls[0][0] == "list"
    assert evolution_client.calls[0][4] == ("category:1", "category:2", "category:3", "category:4")
    assert len(evolution_client.calls) == 1


def test_falls_back_to_numbered_text_when_interactive_delivery_fails() -> None:
    evolution_client = FailingInteractiveEvolutionClient()
    sender = MessageResponseSender(evolution_client=evolution_client)  # type: ignore[arg-type]
    result = ReceiveMediaResult(
        received_message=ReceivedMessage(
            message_id="MSG1",
            sender=Sender(remote_jid="556299999999@s.whatsapp.net"),
            message_type=MessageType.IMAGE,
            raw_type="imageMessage",
        ),
        stored_file=None,
        conversation_state=ConversationState.WAITING_CATEGORY_SELECTION,
        next_message="1 - Sim",
        interactive_prompt=InteractivePrompt(
            text="Escolha",
            options=[InteractiveOption("filename:keep_original", "Manter nome")],
        ),
    )

    delivery = asyncio.run(sender.send_use_case_response(result))

    assert delivery.sent is True
    assert evolution_client.calls == [
        (
            "text",
            "556299999999@s.whatsapp.net",
            "1 - Sim",
        )
    ]
