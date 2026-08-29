import json
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
                pending_media_id=self._encode_pending_media(session),
                updated_at=self._now(),
                allowed_option_ids=session.allowed_option_ids,
                processed_interaction_ids=session.processed_interaction_ids,
                interactive_created_at=session.interactive_created_at,
                created_at=session.created_at,
                expires_at=session.expires_at,
                last_interaction_at=session.last_interaction_at,
                origin=session.origin,
                contact_id=session.contact_id,
                contact_name=session.contact_name,
                greeting_sent=session.greeting_sent,
                expiry_warning_sent=session.expiry_warning_sent,
                received_types=session.received_types,
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
            state=self._state_from_storage(str(row["state"])),
            category=str(row["category"]) if row.get("category") is not None else None,
            filename=str(row["filename"]) if row.get("filename") is not None else None,
            pending_media_id=self._last_pending_media_id(row.get("pending_media_id")),
            pending_media_ids=tuple(self._decode_pending_media(row.get("pending_media_id"))),
            allowed_option_ids=tuple(self._decode_json_list(row.get("allowed_option_ids"))),
            processed_interaction_ids=tuple(self._decode_json_list(row.get("processed_interaction_ids"))),
            interactive_created_at=(
                float(row["interactive_created_at"])
                if row.get("interactive_created_at") is not None
                else None
            ),
            created_at=(
                float(row["created_at"])
                if row.get("created_at") is not None
                else None
            ),
            expires_at=(
                float(row["expires_at"])
                if row.get("expires_at") is not None
                else None
            ),
            last_interaction_at=(
                float(row["last_interaction_at"])
                if row.get("last_interaction_at") is not None
                else None
            ),
            origin=str(row["origin"]) if row.get("origin") is not None else None,
            contact_id=str(row["contact_id"]) if row.get("contact_id") is not None else None,
            contact_name=str(row["contact_name"]) if row.get("contact_name") is not None else None,
            greeting_sent=bool(row.get("greeting_sent")),
            expiry_warning_sent=bool(row.get("expiry_warning_sent")),
            received_types=tuple(self._decode_json_list(row.get("received_types"))),
        )

    def _now(self) -> float:
        return time.time()

    def _state_from_storage(self, state: str) -> ConversationState:
        legacy_states = {
            "FINISHED": ConversationState.FINISHED,
            "PROCESSING": ConversationState.SAVING,
            "WAITING_USAGE_CONFIRMATION": ConversationState.WAITING_CATEGORY_SELECTION,
            "WAITING_CATEGORY": ConversationState.WAITING_CATEGORY_SELECTION,
            "WAITING_CATEGORY_SELECTION": ConversationState.WAITING_CATEGORY_SELECTION,
            "WAITING_FILENAME": ConversationState.WAITING_FILENAME_DECISION,
            "WAITING_FILENAME_DECISION": ConversationState.WAITING_FILENAME_DECISION,
            "WAITING_CUSTOM_FILENAME": ConversationState.WAITING_CUSTOM_FILENAME,
            "WAITING_CONFIRMATION": ConversationState.WAITING_CONFIRMATION,
        }
        if state in legacy_states:
            return legacy_states[state]
        return ConversationState(state)

    def _encode_pending_media(self, session: ConversationSession) -> str | None:
        if session.pending_media_ids:
            return json.dumps(list(session.pending_media_ids))
        return session.pending_media_id

    def _decode_pending_media(self, value: object) -> list[str]:
        if value is None:
            return []
        if not isinstance(value, str):
            return [str(value)]
        text = value.strip()
        if not text:
            return []
        if text.startswith("["):
            return self._decode_json_list(text)
        return [text]

    def _last_pending_media_id(self, value: object) -> str | None:
        pending_media = self._decode_pending_media(value)
        return pending_media[-1] if pending_media else None

    def _decode_json_list(self, value: object) -> list[str]:
        if not isinstance(value, str) or not value:
            return []
        try:
            decoded = json.loads(value)
        except json.JSONDecodeError:
            return []
        if not isinstance(decoded, list):
            return []
        return [str(item) for item in decoded]
