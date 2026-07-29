from threading import RLock
from typing import Protocol

from app.models.persistence import ConversationMessageRecord
from app.services.storage_service import StorageService


class ConversationMessageRepository(Protocol):
    def save(self, message: ConversationMessageRecord) -> None:
        pass

    def list_by_sender(self, sender: str) -> list[ConversationMessageRecord]:
        pass

    def list_recent_contacts(self) -> list[dict[str, object]]:
        pass


class InMemoryConversationMessageRepository:
    def __init__(self) -> None:
        self._messages: list[ConversationMessageRecord] = []
        self._lock = RLock()

    def save(self, message: ConversationMessageRecord) -> None:
        with self._lock:
            self._messages.append(message)

    def list_by_sender(self, sender: str) -> list[ConversationMessageRecord]:
        with self._lock:
            return [message for message in self._messages if message.sender == sender]

    def list_recent_contacts(self) -> list[dict[str, object]]:
        with self._lock:
            contacts: dict[str, dict[str, object]] = {}
            for message in self._messages:
                contact = contacts.setdefault(
                    message.sender,
                    {
                        "sender": message.sender,
                        "last_content": message.content,
                        "last_activity": message.created_at,
                        "message_count": 0,
                        "last_state": message.state,
                        "last_status": message.status.value,
                    },
                )
                contact["last_content"] = message.content
                contact["last_activity"] = message.created_at
                contact["message_count"] = int(contact["message_count"]) + 1
                contact["last_state"] = message.state
                contact["last_status"] = message.status.value

            return list(contacts.values())


class SQLiteConversationMessageRepository:
    def __init__(self, storage_service: StorageService) -> None:
        self._storage_service = storage_service

    def save(self, message: ConversationMessageRecord) -> None:
        self._storage_service.save_conversation_message(
            message_id=message.message_id,
            record_id=message.id,
            sender=message.sender,
            direction=message.direction.value,
            content=message.content,
            message_type=message.message_type,
            state=message.state,
            media_id=message.media_id,
            created_at=message.created_at,
            status=message.status.value,
            error=message.error,
        )

    def list_by_sender(self, sender: str) -> list[ConversationMessageRecord]:
        return [
            self._row_to_record(row)
            for row in self._storage_service.list_conversation_messages(sender)
        ]

    def list_recent_contacts(self) -> list[dict[str, object]]:
        return self._storage_service.list_conversation_contacts()

    def _row_to_record(self, row: dict[str, object]) -> ConversationMessageRecord:
        from app.models.persistence import ConversationMessageDirection, ConversationMessageStatus

        return ConversationMessageRecord(
            id=str(row["id"]),
            message_id=str(row["message_id"]),
            sender=str(row["sender"]),
            direction=ConversationMessageDirection(str(row["direction"])),
            content=str(row["content"]),
            message_type=str(row["message_type"]),
            state=str(row["state"]) if row.get("state") is not None else None,
            media_id=str(row["media_id"]) if row.get("media_id") is not None else None,
            created_at=str(row["created_at"]),
            status=ConversationMessageStatus(str(row["status"])),
            error=str(row["error"]) if row.get("error") is not None else None,
        )
