from collections.abc import Iterator
from contextlib import contextmanager

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.models.message import MessageType, ReceivedMessage, Sender
from app.models.storage import StoredFile
from app.services.application_factory import (
    get_message_response_sender,
    get_receive_media_use_case,
)
from app.services.conversation_engine import ConversationState
from app.services.message_response_sender import MessageDeliveryResult
from app.services.receive_media_use_case import ReceiveMediaResult
from app.api.webhooks import settings


class FakeReceiveMediaUseCase:
    def __init__(self, result: ReceiveMediaResult | Exception) -> None:
        self.result = result

    async def execute(self, payload: dict[str, object]) -> ReceiveMediaResult:
        if isinstance(self.result, Exception):
            raise self.result

        return self.result


class FakeMessageResponseSender:
    def __init__(self, result: MessageDeliveryResult | Exception | None = None) -> None:
        self.result = result or MessageDeliveryResult(sent=True)
        self.calls: list[ReceiveMediaResult] = []

    async def send_use_case_response(
        self,
        result: ReceiveMediaResult,
    ) -> MessageDeliveryResult:
        self.calls.append(result)
        if result.received_message is None or not result.next_message:
            return MessageDeliveryResult(sent=False)

        if isinstance(self.result, Exception):
            raise self.result

        return self.result


@contextmanager
def _client_with_use_case(
    use_case: FakeReceiveMediaUseCase,
    response_sender: FakeMessageResponseSender | None = None,
    webhook_secret: str = "",
) -> Iterator[TestClient]:
    original_secret = settings.WEBHOOK_SECRET
    settings.WEBHOOK_SECRET = webhook_secret
    response_sender = response_sender or FakeMessageResponseSender()
    app.dependency_overrides[get_receive_media_use_case] = lambda: use_case
    app.dependency_overrides[get_message_response_sender] = lambda: response_sender
    try:
        yield TestClient(app)
    finally:
        settings.WEBHOOK_SECRET = original_secret
        app.dependency_overrides.clear()


def _payload(message: dict[str, object]) -> dict[str, object]:
    return {
        "event": "messages.upsert",
        "data": {
            "key": {
                "id": "MSG1",
                "remoteJid": "556299999999@s.whatsapp.net",
                "fromMe": False,
            },
            "message": message,
        },
    }


def _received_message(message_type: MessageType = MessageType.TEXT) -> ReceivedMessage:
    return ReceivedMessage(
        message_id="MSG1",
        sender=Sender(remote_jid="556299999999@s.whatsapp.net"),
        message_type=message_type,
        raw_type="conversation",
        text="Ola" if message_type is MessageType.TEXT else None,
    )


def _stored_file() -> StoredFile:
    return StoredFile(
        absolute_path="C:\\media\\arquivo.jpg",
        relative_path="arquivo.jpg",
        file_name="arquivo.jpg",
        extension=".jpg",
        size_bytes=10,
        sha256="hash",
    )


def _result(
    received_message: ReceivedMessage | None = None,
    stored_file: StoredFile | None = None,
    errors: list[str] | None = None,
) -> ReceiveMediaResult:
    return ReceiveMediaResult(
        received_message=received_message,
        stored_file=stored_file,
        conversation_state=ConversationState.WAITING_CATEGORY_SELECTION if received_message else None,
        next_message="Recebi seu arquivo. Como deseja classifica-lo?" if received_message else None,
        errors=errors or [],
    )


def test_webhook_authorized() -> None:
    use_case = FakeReceiveMediaUseCase(_result(received_message=_received_message()))
    response_sender = FakeMessageResponseSender()

    with _client_with_use_case(use_case, response_sender=response_sender) as client:
        response = client.post("/webhooks/evolution", json=_payload({"conversation": "Ola"}))

    assert response.status_code == 200
    assert response.json()["received"] is True
    assert response.json()["message_sent"] is True
    assert len(response_sender.calls) == 1


def test_webhook_unauthorized() -> None:
    use_case = FakeReceiveMediaUseCase(_result(received_message=_received_message()))

    with _client_with_use_case(use_case, webhook_secret="secret") as client:
        response = client.post(
            "/webhooks/evolution",
            headers={"x-webhook-secret": "wrong"},
            json=_payload({"conversation": "Ola"}),
        )

    assert response.status_code == 401
    assert response.json()["detail"] == "Webhook não autorizado."


def test_webhook_valid_text_payload() -> None:
    use_case = FakeReceiveMediaUseCase(_result(received_message=_received_message(MessageType.TEXT)))

    with _client_with_use_case(use_case) as client:
        response = client.post("/webhooks/evolution", json=_payload({"conversation": "Ola"}))

    body = response.json()
    assert response.status_code == 200
    assert body["processed"] is True
    assert body["conversation_state"] == ConversationState.WAITING_CATEGORY_SELECTION.value
    assert body["next_message"] == "Recebi seu arquivo. Como deseja classifica-lo?"
    assert body["has_file"] is False
    assert body["message_sent"] is True
    assert body["has_errors"] is False


def test_webhook_valid_media_payload() -> None:
    use_case = FakeReceiveMediaUseCase(
        _result(received_message=_received_message(MessageType.IMAGE), stored_file=_stored_file())
    )

    with _client_with_use_case(use_case) as client:
        response = client.post("/webhooks/evolution", json=_payload({"imageMessage": {"mimetype": "image/jpeg"}}))

    body = response.json()
    assert response.status_code == 200
    assert body["processed"] is True
    assert body["has_file"] is True
    assert body["message_sent"] is True
    assert "absolute_path" not in body
    assert "content" not in body


def test_webhook_invalid_payload() -> None:
    use_case = FakeReceiveMediaUseCase(_result(errors=["mensagem_invalida"]))

    with _client_with_use_case(use_case) as client:
        response = client.post("/webhooks/evolution", json={"event": "messages.upsert", "data": None})

    body = response.json()
    assert response.status_code == 200
    assert body["processed"] is False
    assert body["conversation_state"] is None
    assert body["next_message"] is None
    assert body["message_sent"] is False
    assert body["has_errors"] is True


def test_webhook_controlled_pipeline_failure() -> None:
    use_case = FakeReceiveMediaUseCase(
        _result(
            received_message=_received_message(MessageType.IMAGE),
            errors=["download: falha controlada"],
        )
    )

    with _client_with_use_case(use_case) as client:
        response = client.post("/webhooks/evolution", json=_payload({"imageMessage": {"mimetype": "image/jpeg"}}))

    body = response.json()
    assert response.status_code == 200
    assert body["processed"] is True
    assert body["has_file"] is False
    assert body["message_sent"] is True
    assert body["has_errors"] is True


def test_webhook_controlled_delivery_failure() -> None:
    use_case = FakeReceiveMediaUseCase(_result(received_message=_received_message()))
    response_sender = FakeMessageResponseSender(
        MessageDeliveryResult(sent=False, error="Evolution API returned HTTP 500.")
    )

    with _client_with_use_case(use_case, response_sender=response_sender) as client:
        response = client.post("/webhooks/evolution", json=_payload({"conversation": "Ola"}))

    body = response.json()
    assert response.status_code == 200
    assert body["processed"] is True
    assert body["message_sent"] is False
    assert body["has_errors"] is True


def test_webhook_does_not_hide_programming_errors() -> None:
    use_case = FakeReceiveMediaUseCase(RuntimeError("bug inesperado"))

    with _client_with_use_case(use_case) as client:
        with pytest.raises(RuntimeError):
            client.post("/webhooks/evolution", json=_payload({"conversation": "Ola"}))
