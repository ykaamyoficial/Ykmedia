from typing import Any

from app.models.message import MessageType
from app.models.interactive import InteractionSource
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


def test_maps_contact_name_from_push_name() -> None:
    payload = _payload({"conversation": "Ola"})
    payload["data"]["pushName"] = "Joao Silva"

    result = map_evolution_payload(payload)

    assert result.message is not None
    assert result.message.sender.display_name == "Joao Silva"


def test_maps_extended_text_payload_to_domain_message() -> None:
    result = map_evolution_payload(_payload({"extendedTextMessage": {"text": "Ola"}}))

    assert result.message is not None
    assert result.message.message_type is MessageType.TEXT
    assert result.message.text == "Ola"


def test_maps_button_reply_payload_to_normalized_interaction() -> None:
    result = map_evolution_payload(
        _payload(
            {
                "buttonsResponseMessage": {
                    "selectedButtonId": "category:1",
                    "selectedDisplayText": "Louvores",
                }
            }
        )
    )

    assert result.message is not None
    assert result.message.message_type is MessageType.TEXT
    assert result.message.interaction is not None
    assert result.message.interaction.option_id == "category:1"
    assert result.message.interaction.option_title == "Louvores"
    assert result.message.interaction.source_type is InteractionSource.BUTTON_REPLY


def test_maps_list_reply_payload_to_normalized_interaction() -> None:
    result = map_evolution_payload(
        _payload(
            {
                "listResponseMessage": {
                    "title": "Mensagens",
                    "singleSelectReply": {"selectedRowId": "category:2"},
                }
            }
        )
    )

    assert result.message is not None
    assert result.message.interaction is not None
    assert result.message.interaction.option_id == "category:2"
    assert result.message.interaction.option_title == "Mensagens"
    assert result.message.interaction.source_type is InteractionSource.LIST_REPLY


def test_maps_media_payload_to_domain_message() -> None:
    result = map_evolution_payload(
        _payload({"documentMessage": {"mimetype": "application/pdf", "fileName": "arquivo.pdf"}})
    )

    assert result.message is not None
    assert result.message.message_type is MessageType.DOCUMENT
    assert result.message.media is not None
    assert result.message.media.mimetype == "application/pdf"
    assert result.message.media.file_name == "arquivo.pdf"


def test_maps_wrapped_media_payload_to_domain_message() -> None:
    result = map_evolution_payload(
        _payload(
            {
                "ephemeralMessage": {
                    "message": {
                        "imageMessage": {
                            "mimetype": "image/jpeg",
                            "mediaKey": "media-key",
                        }
                    }
                }
            }
        )
    )

    assert result.message is not None
    assert result.message.message_type is MessageType.IMAGE
    assert result.message.raw_type == "imageMessage"
    assert result.message.media is not None
    assert result.message.media.mimetype == "image/jpeg"


def test_maps_media_payload_with_download_reference_without_mimetype() -> None:
    result = map_evolution_payload(
        _payload({"imageMessage": {"mediaKey": "media-key", "directPath": "/media/path"}})
    )

    assert result.message is not None
    assert result.message.message_type is MessageType.IMAGE
    assert result.message.media is not None
    assert result.message.media.metadata == {"mediaKey": "media-key", "directPath": "/media/path"}


def test_maps_sticker_payload_to_sticker_domain_message() -> None:
    result = map_evolution_payload(_payload({"stickerMessage": {"mimetype": "image/webp"}}))

    assert result.message is not None
    assert result.message.message_type is MessageType.STICKER
    assert result.message.raw_type == "stickerMessage"


def test_maps_gif_video_payload_to_gif_domain_message() -> None:
    result = map_evolution_payload(_payload({"videoMessage": {"mimetype": "video/mp4", "gifPlayback": True}}))

    assert result.message is not None
    assert result.message.message_type is MessageType.GIF
    assert result.message.raw_type == "videoMessage"


def test_ignores_group_message() -> None:
    payload = _payload({"imageMessage": {"mimetype": "image/jpeg"}})
    payload["data"]["key"]["remoteJid"] = "556299999999-123@g.us"

    result = map_evolution_payload(payload)

    assert result.is_ignored is True
    assert result.ignored_reason == "mensagem_grupo"


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
