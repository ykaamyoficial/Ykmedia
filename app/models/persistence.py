from dataclasses import dataclass

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
