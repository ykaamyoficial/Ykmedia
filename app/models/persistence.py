from dataclasses import dataclass
from enum import StrEnum

from app.services.conversation_engine import ConversationState


@dataclass(frozen=True, slots=True)
class MediaRecord:
    media_id: str
    message_id: str
    file_name: str
    relative_path: str
    mimetype: str | None
    size_bytes: int
    sha256: str
    absolute_path: str | None = None


@dataclass(frozen=True, slots=True)
class ConversationRecord:
    sender_id: str
    state: ConversationState
    is_active: bool = True


class ProcessedMessageStatus(StrEnum):
    PROCESSING = "PROCESSANDO"
    COMPLETED = "CONCLUIDO"
    ERROR = "ERRO"


@dataclass(frozen=True, slots=True)
class ProcessedMessageRecord:
    message_id: str
    sender: str
    status: ProcessedMessageStatus
    processed_at: str
    error: str | None = None


class ConversationMessageDirection(StrEnum):
    INBOUND = "INBOUND"
    OUTBOUND = "OUTBOUND"


class ConversationMessageStatus(StrEnum):
    RECEIVED = "RECEBIDA"
    SENT = "ENVIADA"
    ERROR = "ERRO"


@dataclass(frozen=True, slots=True)
class ConversationMessageRecord:
    id: str
    message_id: str
    sender: str
    direction: ConversationMessageDirection
    content: str
    message_type: str
    state: str | None
    media_id: str | None
    created_at: str
    status: ConversationMessageStatus
    error: str | None = None
