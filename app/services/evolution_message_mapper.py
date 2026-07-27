from dataclasses import dataclass
from typing import Any

from app.models.message import Media, MessageType, ReceivedMessage, Sender

SUPPORTED_EVENTS = {"messages.upsert", "messages_upsert"}


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
    )

    if sender.is_from_me:
        return EvolutionMessageMappingResult(message=None, ignored_reason="mensagem_propria")

    message_payload = data.get("message") or {}
    if not isinstance(message_payload, dict):
        message_payload = {}

    raw_type = str(next(iter(message_payload), "unknown"))
    content = message_payload.get(raw_type) if raw_type in message_payload else {}

    message = ReceivedMessage(
        message_id=str(key.get("id") or ""),
        sender=sender,
        message_type=_identify_message_type(raw_type),
        raw_type=raw_type,
        text=_extract_text(raw_type, content),
        media=_extract_media(content),
    )

    return EvolutionMessageMappingResult(message=message, event=event)


def _event_name(payload: dict[str, Any]) -> str:
    return str(payload.get("event") or "").strip().lower()


def _identify_message_type(raw_type: str) -> MessageType:
    message_types = {
        "conversation": MessageType.TEXT,
        "extendedTextMessage": MessageType.TEXT,
        "imageMessage": MessageType.IMAGE,
        "audioMessage": MessageType.AUDIO,
        "videoMessage": MessageType.VIDEO,
        "documentMessage": MessageType.DOCUMENT,
    }
    return message_types.get(raw_type, MessageType.UNKNOWN)


def _extract_text(raw_type: str, content: Any) -> str | None:
    if raw_type == "conversation":
        return str(content) if content is not None else ""

    if raw_type == "extendedTextMessage" and isinstance(content, dict):
        return str(content.get("text") or "")

    return None


def _extract_media(content: Any) -> Media | None:
    if not isinstance(content, dict):
        return None

    mimetype = content.get("mimetype")
    file_name = content.get("fileName")
    caption = content.get("caption")

    if not any((mimetype, file_name, caption)):
        return None

    return Media(
        mimetype=str(mimetype) if mimetype else None,
        file_name=str(file_name) if file_name else None,
        caption=str(caption) if caption else None,
        metadata=content,
    )
