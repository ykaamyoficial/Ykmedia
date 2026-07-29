from datetime import datetime, timezone
from threading import RLock
from typing import Protocol

from app.models.persistence import ProcessedMessageRecord, ProcessedMessageStatus
from app.services.storage_service import StorageService


class ProcessedMessageRepository(Protocol):
    def start(self, message_id: str, sender: str) -> bool:
        pass

    def complete(self, message_id: str) -> None:
        pass

    def fail(self, message_id: str, error: str) -> None:
        pass

    def get(self, message_id: str) -> ProcessedMessageRecord | None:
        pass

    def exists(self, message_id: str) -> bool:
        pass


class InMemoryProcessedMessageRepository:
    def __init__(self) -> None:
        self._records: dict[str, ProcessedMessageRecord] = {}
        self._lock = RLock()

    def start(self, message_id: str, sender: str) -> bool:
        if not message_id:
            return True

        with self._lock:
            current = self._records.get(message_id)
            if current is not None and current.status is not ProcessedMessageStatus.ERROR:
                return False

            self._records[message_id] = ProcessedMessageRecord(
                message_id=message_id,
                sender=sender,
                status=ProcessedMessageStatus.PROCESSING,
                processed_at=_now_iso(),
            )
            return True

    def complete(self, message_id: str) -> None:
        self._set_status(message_id, ProcessedMessageStatus.COMPLETED)

    def fail(self, message_id: str, error: str) -> None:
        self._set_status(message_id, ProcessedMessageStatus.ERROR, error=error)

    def get(self, message_id: str) -> ProcessedMessageRecord | None:
        with self._lock:
            return self._records.get(message_id)

    def exists(self, message_id: str) -> bool:
        with self._lock:
            return message_id in self._records

    def _set_status(
        self,
        message_id: str,
        status: ProcessedMessageStatus,
        error: str | None = None,
    ) -> None:
        if not message_id:
            return

        with self._lock:
            current = self._records.get(message_id)
            sender = current.sender if current is not None else ""
            self._records[message_id] = ProcessedMessageRecord(
                message_id=message_id,
                sender=sender,
                status=status,
                processed_at=_now_iso(),
                error=error,
            )


class SQLiteProcessedMessageRepository:
    def __init__(self, storage_service: StorageService) -> None:
        self._storage_service = storage_service
        self._lock = RLock()

    def start(self, message_id: str, sender: str) -> bool:
        if not message_id:
            return True

        with self._lock:
            current = self.get(message_id)
            if current is not None and current.status is not ProcessedMessageStatus.ERROR:
                return False

            self._storage_service.save_processed_message(
                message_id=message_id,
                sender=sender,
                status=ProcessedMessageStatus.PROCESSING.value,
                processed_at=_now_iso(),
                error=None,
            )
            return True

    def complete(self, message_id: str) -> None:
        self._set_status(message_id, ProcessedMessageStatus.COMPLETED)

    def fail(self, message_id: str, error: str) -> None:
        self._set_status(message_id, ProcessedMessageStatus.ERROR, error=error)

    def get(self, message_id: str) -> ProcessedMessageRecord | None:
        row = self._storage_service.get_processed_message(message_id)
        if row is None:
            return None

        return ProcessedMessageRecord(
            message_id=str(row["message_id"]),
            sender=str(row["sender"]),
            status=ProcessedMessageStatus(str(row["status"])),
            processed_at=str(row["processed_at"]),
            error=str(row["error"]) if row.get("error") is not None else None,
        )

    def exists(self, message_id: str) -> bool:
        return self.get(message_id) is not None

    def _set_status(
        self,
        message_id: str,
        status: ProcessedMessageStatus,
        error: str | None = None,
    ) -> None:
        if not message_id:
            return

        current = self.get(message_id)
        self._storage_service.save_processed_message(
            message_id=message_id,
            sender=current.sender if current is not None else "",
            status=status.value,
            processed_at=_now_iso(),
            error=error,
        )


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()
