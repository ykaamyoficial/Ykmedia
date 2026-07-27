import time

from app.services.conversation_engine import ConversationSession, ConversationState
from app.services.session_store import MemorySessionStore


def test_creates_session() -> None:
    store = MemorySessionStore()

    session = store.create("sender-1")

    assert session.state is ConversationState.IDLE
    assert store.exists("sender-1") is True


def test_recovers_session() -> None:
    store = MemorySessionStore()
    created_session = store.create("sender-1")

    recovered_session = store.get("sender-1")

    assert recovered_session is created_session


def test_updates_session() -> None:
    store = MemorySessionStore()
    session = ConversationSession(state=ConversationState.WAITING_FILENAME, category="musica")

    store.update("sender-1", session)

    recovered_session = store.get("sender-1")
    assert recovered_session == session


def test_removes_session() -> None:
    store = MemorySessionStore()
    store.create("sender-1")

    store.remove("sender-1")

    assert store.exists("sender-1") is False
    assert store.get("sender-1") is None


def test_expires_session_by_ttl() -> None:
    store = MemorySessionStore(ttl_seconds=0.01)
    store.create("sender-1")

    time.sleep(0.02)

    assert store.get("sender-1") is None
    assert store.exists("sender-1") is False


def test_handles_multiple_sessions_simultaneously() -> None:
    store = MemorySessionStore()
    first_session = store.create("sender-1")
    second_session = store.create("sender-2")

    first_session.state = ConversationState.WAITING_CATEGORY
    second_session.state = ConversationState.WAITING_FILENAME
    store.update("sender-1", first_session)
    store.update("sender-2", second_session)

    assert store.get("sender-1").state is ConversationState.WAITING_CATEGORY  # type: ignore[union-attr]
    assert store.get("sender-2").state is ConversationState.WAITING_FILENAME  # type: ignore[union-attr]


def test_clear_expired_returns_removed_count() -> None:
    store = MemorySessionStore(ttl_seconds=0.01)
    store.create("sender-1")
    store.create("sender-2")
    time.sleep(0.02)

    removed_count = store.clear_expired()

    assert removed_count == 2
