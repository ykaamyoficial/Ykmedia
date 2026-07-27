from typing import Any

from app.models.message import MessageType
from app.services.evolution_message_mapper import map_evolution_payload


def _payload(message: dict[str, Any]) -> dict[str, Any]:
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


def test_maps_text_payload_to_domain_message() -> None:
    result = map_evolution_payload(_payload({"conversation": "Ola"}))

    assert result.message is not None
    assert result.message.message_id == "MSG1"
    assert result.message.sender.remote_jid == "556299999999@s.whatsapp.net"
    assert result.message.message_type is MessageType.TEXT
    assert result.message.raw_type == "conversation"
    assert result.message.text == "Ola"


def test_maps_extended_text_payload_to_domain_message() -> None:
    result = map_evolution_payload(_payload({"extendedTextMessage": {"text": "Ola"}}))

    assert result.message is not None
    assert result.message.message_type is MessageType.TEXT
    assert result.message.text == "Ola"


def test_maps_media_payload_to_domain_message() -> None:
    result = map_evolution_payload(
        _payload({"documentMessage": {"mimetype": "application/pdf", "fileName": "arquivo.pdf"}})
    )

    assert result.message is not None
    assert result.message.message_type is MessageType.DOCUMENT
    assert result.message.media is not None
    assert result.message.media.mimetype == "application/pdf"
    assert result.message.media.file_name == "arquivo.pdf"


def test_maps_unknown_payload_to_unknown_domain_message() -> None:
    result = map_evolution_payload(_payload({"stickerMessage": {"mimetype": "image/webp"}}))

    assert result.message is not None
    assert result.message.message_type is MessageType.UNKNOWN
    assert result.message.raw_type == "stickerMessage"


def test_maps_unsupported_event_to_ignored_result() -> None:
    result = map_evolution_payload({"event": "connection.update", "data": {}})

    assert result.is_ignored is True
    assert result.ignored_reason == "evento_ignorado"
    assert result.event == "connection.update"


def test_maps_invalid_payload_to_ignored_result() -> None:
    result = map_evolution_payload({"event": "messages.upsert", "data": None})

    assert result.is_ignored is True
    assert result.ignored_reason == "mensagem_invalida"


def test_maps_own_message_to_ignored_result() -> None:
    payload = _payload({"conversation": "teste"})
    payload["data"]["key"]["fromMe"] = True

    result = map_evolution_payload(payload)

    assert result.is_ignored is True
    assert result.ignored_reason == "mensagem_propria"
