from threading import RLock
from typing import Protocol

from app.models.persistence import ConversationRecord


class ConversationRepository(Protocol):
    def save(self, conversation: ConversationRecord) -> None:
        pass

    def get(self, sender_id: str) -> ConversationRecord | None:
        pass

    def delete(self, sender_id: str) -> None:
        pass

    def list_active(self) -> list[ConversationRecord]:
        pass


class InMemoryConversationRepository:
    def __init__(self) -> None:
        self._records: dict[str, ConversationRecord] = {}
        self._lock = RLock()

    def save(self, conversation: ConversationRecord) -> None:
        with self._lock:
            self._records[conversation.sender_id] = conversation

    def get(self, sender_id: str) -> ConversationRecord | None:
        with self._lock:
            return self._records.get(sender_id)

    def delete(self, sender_id: str) -> None:
        with self._lock:
            self._records.pop(sender_id, None)

    def list_active(self) -> list[ConversationRecord]:
        with self._lock:
            return [
                conversation
                for conversation in self._records.values()
                if conversation.is_active
            ]
