import time
from dataclasses import dataclass
from threading import RLock
from typing import Protocol

from app.services.conversation_engine import ConversationSession, ConversationState
from app.services.storage_service import StorageService


class SessionStore(Protocol):
    def get(self, sender_id: str) -> ConversationSession | None:
        pass

    def create(self, sender_id: str) -> ConversationSession:
        pass

    def update(self, sender_id: str, session: ConversationSession) -> None:
        pass

    def remove(self, sender_id: str) -> None:
        pass

    def exists(self, sender_id: str) -> bool:
        pass

    def clear_expired(self) -> int:
        pass


@dataclass(slots=True)
class _StoredSession:
    session: ConversationSession
    updated_at: float


class MemorySessionStore:
    def __init__(self, ttl_seconds: float = 3600.0) -> None:
        if ttl_seconds <= 0:
            raise ValueError("ttl_seconds must be greater than zero.")

        self._ttl_seconds = ttl_seconds
        self._sessions: dict[str, _StoredSession] = {}
        self._lock = RLock()

    def get(self, sender_id: str) -> ConversationSession | None:
        with self._lock:
            self.clear_expired()
            stored_session = self._sessions.get(sender_id)
            if stored_session is None:
                return None

            stored_session.updated_at = self._now()
            return stored_session.session

    def create(self, sender_id: str) -> ConversationSession:
        with self._lock:
            self.clear_expired()
            session = ConversationSession()
            self._sessions[sender_id] = _StoredSession(
                session=session,
                updated_at=self._now(),
            )
            return session

    def update(self, sender_id: str, session: ConversationSession) -> None:
        with self._lock:
            self.clear_expired()
            self._sessions[sender_id] = _StoredSession(
                session=session,
                updated_at=self._now(),
            )

    def remove(self, sender_id: str) -> None:
        with self._lock:
            self.clear_expired()
            self._sessions.pop(sender_id, None)

    def exists(self, sender_id: str) -> bool:
        with self._lock:
            self.clear_expired()
            return sender_id in self._sessions

    def clear_expired(self) -> int:
        with self._lock:
            now = self._now()
            expired_sender_ids = [
                sender_id
                for sender_id, stored_session in self._sessions.items()
                if now - stored_session.updated_at >= self._ttl_seconds
            ]

            for sender_id in expired_sender_ids:
                self._sessions.pop(sender_id, None)

            return len(expired_sender_ids)

    def _now(self) -> float:
        return time.monotonic()


class SQLiteSessionStore:
    def __init__(self, storage_service: StorageService, ttl_seconds: float = 3600.0) -> None:
        if ttl_seconds <= 0:
            raise ValueError("ttl_seconds must be greater than zero.")

        self._storage_service = storage_service
        self._ttl_seconds = ttl_seconds
        self._lock = RLock()

    def get(self, sender_id: str) -> ConversationSession | None:
        with self._lock:
            self.clear_expired()
            row = self._storage_service.get_session(sender_id)
            if row is None:
                return None

            session = self._row_to_session(row)
            self.update(sender_id, session)
            return session

    def create(self, sender_id: str) -> ConversationSession:
        with self._lock:
            self.clear_expired()
            session = ConversationSession()
            self.update(sender_id, session)
            return session

    def update(self, sender_id: str, session: ConversationSession) -> None:
        with self._lock:
            self.clear_expired()
            self._storage_service.save_session(
                sender_id=sender_id,
                state=session.state.value,
                category=session.category,
                filename=session.filename,
                updated_at=self._now(),
            )

    def remove(self, sender_id: str) -> None:
        with self._lock:
            self.clear_expired()
            self._storage_service.delete_session(sender_id)

    def exists(self, sender_id: str) -> bool:
        with self._lock:
            self.clear_expired()
            return self._storage_service.get_session(sender_id) is not None

    def clear_expired(self) -> int:
        with self._lock:
            expires_before = self._now() - self._ttl_seconds
            return self._storage_service.delete_expired_sessions(expires_before)

    def _row_to_session(self, row: dict[str, object]) -> ConversationSession:
        return ConversationSession(
            state=ConversationState(str(row["state"])),
            category=str(row["category"]) if row.get("category") is not None else None,
            filename=str(row["filename"]) if row.get("filename") is not None else None,
        )

    def _now(self) -> float:
        return time.time()
