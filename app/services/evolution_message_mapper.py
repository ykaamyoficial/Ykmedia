from dataclasses import dataclass
import logging
from typing import Any

from app.models.interactive import IncomingInteraction, InteractionSource
from app.models.message import Media, MessageType, ReceivedMessage, Sender

SUPPORTED_EVENTS = {"messages.upsert", "messages_upsert"}
SUPPORTED_MESSAGE_TYPES = (
    "conversation",
    "extendedTextMessage",
    "imageMessage",
    "audioMessage",
    "videoMessage",
    "documentMessage",
    "stickerMessage",
    "contactMessage",
    "contactsArrayMessage",
    "locationMessage",
    "liveLocationMessage",
    "editedMessage",
    "reactionMessage",
    "buttonsResponseMessage",
    "templateButtonReplyMessage",
    "listResponseMessage",
)
MESSAGE_WRAPPERS = (
    "ephemeralMessage",
    "viewOnceMessage",
    "viewOnceMessageV2",
    "documentWithCaptionMessage",
)

logger = logging.getLogger(__name__)


@dataclass(frozen=True, slots=True)
class EvolutionMessageMappingResult:
    message: ReceivedMessage | None
    ignored_reason: str | None = None
    event: str | None = None

    @property
    def is_ignored(self) -> bool:
        return self.message is None


def map_evolution_payload(payload: dict[str, Any]) -> EvolutionMessageMappingResult:
    event = _event_name(payload)
    if event not in SUPPORTED_EVENTS:
        return EvolutionMessageMappingResult(
            message=None,
            ignored_reason="evento_ignorado",
            event=event,
        )

    data = payload.get("data")
    if not isinstance(data, dict):
        return EvolutionMessageMappingResult(message=None, ignored_reason="mensagem_invalida")

    key = data.get("key")
    if not isinstance(key, dict):
        return EvolutionMessageMappingResult(message=None, ignored_reason="mensagem_invalida")

    sender = Sender(
        remote_jid=str(key.get("remoteJid") or ""),
        is_from_me=bool(key.get("fromMe")),
        is_group=str(key.get("remoteJid") or "").endswith("@g.us"),
        display_name=_extract_contact_name(data),
        profile_picture_url=_extract_profile_picture_url(data),
    )

    if sender.is_from_me:
        return EvolutionMessageMappingResult(message=None, ignored_reason="mensagem_propria")

    if sender.is_group:
        logger.info("Mensagem ignorada: origem = grupo.")
        return EvolutionMessageMappingResult(message=None, ignored_reason="mensagem_grupo")

    message_payload = data.get("message") or {}
    if not isinstance(message_payload, dict):
        message_payload = {}

    raw_type, content = _extract_message_content(message_payload)

    message = ReceivedMessage(
        message_id=str(key.get("id") or ""),
        sender=sender,
        message_type=_identify_message_type(raw_type, content),
        raw_type=raw_type,
        text=_extract_text(raw_type, content),
        media=_extract_media(content),
        interaction=_extract_interaction(raw_type, content),
    )

    return EvolutionMessageMappingResult(message=message, event=event)


def _event_name(payload: dict[str, Any]) -> str:
    return str(payload.get("event") or "").strip().lower()


def _extract_contact_name(data: dict[str, Any]) -> str | None:
    for key in ("pushName", "notifyName", "contactName", "senderName"):
        value = data.get(key)
        if isinstance(value, str) and value.strip():
            return value.strip()
    return None


def _extract_profile_picture_url(data: dict[str, Any]) -> str | None:
    for key in ("profilePictureUrl", "profilePicUrl", "pictureUrl"):
        value = data.get(key)
        if isinstance(value, str) and value.strip():
            return value.strip()
    return None


def _identify_message_type(raw_type: str, content: Any) -> MessageType:
    if raw_type == "videoMessage" and isinstance(content, dict) and bool(content.get("gifPlayback")):
        return MessageType.GIF

    message_types = {
        "conversation": MessageType.TEXT,
        "extendedTextMessage": MessageType.TEXT,
        "imageMessage": MessageType.IMAGE,
        "audioMessage": MessageType.AUDIO,
        "videoMessage": MessageType.VIDEO,
        "documentMessage": MessageType.DOCUMENT,
        "stickerMessage": MessageType.STICKER,
        "contactMessage": MessageType.CONTACT,
        "contactsArrayMessage": MessageType.CONTACT,
        "locationMessage": MessageType.LOCATION,
        "liveLocationMessage": MessageType.LOCATION,
        "editedMessage": MessageType.EDITED,
        "reactionMessage": MessageType.REACTION,
        "buttonsResponseMessage": MessageType.TEXT,
        "templateButtonReplyMessage": MessageType.TEXT,
        "listResponseMessage": MessageType.TEXT,
    }
    return message_types.get(raw_type, MessageType.UNKNOWN)


def _extract_message_content(message_payload: dict[str, Any]) -> tuple[str, Any]:
    for message_type in SUPPORTED_MESSAGE_TYPES:
        if message_type in message_payload:
            return message_type, message_payload.get(message_type)

    for wrapper in MESSAGE_WRAPPERS:
        wrapper_payload = message_payload.get(wrapper)
        if not isinstance(wrapper_payload, dict):
            continue

        nested_message = wrapper_payload.get("message")
        if isinstance(nested_message, dict):
            return _extract_message_content(nested_message)

    raw_type = str(next(iter(message_payload), "unknown"))
    return raw_type, message_payload.get(raw_type) if raw_type in message_payload else {}


def _extract_text(raw_type: str, content: Any) -> str | None:
    if raw_type == "conversation":
        return str(content) if content is not None else ""

    if raw_type == "extendedTextMessage" and isinstance(content, dict):
        return str(content.get("text") or "")

    if raw_type in {"buttonsResponseMessage", "templateButtonReplyMessage"} and isinstance(content, dict):
        return str(content.get("selectedDisplayText") or content.get("selectedButtonId") or content.get("selectedId") or "")

    if raw_type == "listResponseMessage" and isinstance(content, dict):
        reply = content.get("singleSelectReply")
        if isinstance(reply, dict):
            return str(content.get("title") or reply.get("selectedRowId") or "")
        return str(content.get("title") or "")

    return None


def _extract_interaction(raw_type: str, content: Any) -> IncomingInteraction | None:
    if raw_type == "buttonsResponseMessage" and isinstance(content, dict):
        option_id = content.get("selectedButtonId")
        if isinstance(option_id, str) and option_id.strip():
            return IncomingInteraction(
                option_id=option_id.strip(),
                option_title=_optional_text(content.get("selectedDisplayText")),
                source_type=InteractionSource.BUTTON_REPLY,
            )

    if raw_type == "templateButtonReplyMessage" and isinstance(content, dict):
        option_id = content.get("selectedId")
        if isinstance(option_id, str) and option_id.strip():
            return IncomingInteraction(
                option_id=option_id.strip(),
                option_title=_optional_text(content.get("selectedDisplayText")),
                source_type=InteractionSource.BUTTON_REPLY,
            )

    if raw_type == "listResponseMessage" and isinstance(content, dict):
        reply = content.get("singleSelectReply")
        if isinstance(reply, dict):
            option_id = reply.get("selectedRowId")
            if isinstance(option_id, str) and option_id.strip():
                return IncomingInteraction(
                    option_id=option_id.strip(),
                    option_title=_optional_text(content.get("title")),
                    source_type=InteractionSource.LIST_REPLY,
                )

    return None


def _optional_text(value: Any) -> str | None:
    if isinstance(value, str) and value.strip():
        return value.strip()
    return None


def _extract_media(content: Any) -> Media | None:
    if not isinstance(content, dict):
        return None

    mimetype = content.get("mimetype")
    file_name = content.get("fileName")
    caption = content.get("caption")

    has_media_reference = any(
        content.get(key)
        for key in (
            "mediaKey",
            "directPath",
            "url",
            "fileSha256",
            "fileEncSha256",
        )
    )

    if not any((mimetype, file_name, caption, has_media_reference)):
        return None

    return Media(
        mimetype=str(mimetype) if mimetype else None,
        file_name=str(file_name) if file_name else None,
        caption=str(caption) if caption else None,
        metadata=content,
    )
