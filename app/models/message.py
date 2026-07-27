from dataclasses import dataclass
from enum import StrEnum
from typing import Any


class MessageType(StrEnum):
    TEXT = "texto"
    IMAGE = "imagem"
    AUDIO = "audio"
    VIDEO = "video"
    DOCUMENT = "documento"
    UNKNOWN = "desconhecida"


@dataclass(frozen=True, slots=True)
class Sender:
    remote_jid: str
    is_from_me: bool = False


@dataclass(frozen=True, slots=True)
class Media:
    mimetype: str | None = None
    file_name: str | None = None
    caption: str | None = None
    metadata: dict[str, Any] | None = None


@dataclass(frozen=True, slots=True)
class ReceivedMessage:
    message_id: str
    sender: Sender
    message_type: MessageType
    raw_type: str
    text: str | None = None
    media: Media | None = None
