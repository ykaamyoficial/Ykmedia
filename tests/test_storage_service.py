from pathlib import Path

from app.services.category_service import CategoryService
from app.services.conversation_engine import ConversationSession, ConversationState
from app.services.processing_queue import ProcessingJobOrigin, ProcessingQueue
from app.services.session_store import SQLiteSessionStore
from app.services.storage_service import StorageService


def test_creates_database_automatically(tmp_path: Path) -> None:
    database_path = tmp_path / "ykmedia.sqlite3"

    StorageService(database_path=database_path)

    assert database_path.exists()


def test_persists_categories_after_restart(tmp_path: Path) -> None:
    database_path = tmp_path / "ykmedia.sqlite3"
    storage = StorageService(database_path=database_path)
    category_service = CategoryService(storage_service=storage)
    category_service.add("Eventos")

    restarted_service = CategoryService(storage_service=StorageService(database_path=database_path))

    assert "Eventos" in restarted_service.list_categories()


def test_persists_processing_queue_after_restart(tmp_path: Path) -> None:
    database_path = tmp_path / "ykmedia.sqlite3"
    storage = StorageService(database_path=database_path)
    queue = ProcessingQueue(storage_service=storage)
    job = queue.enqueue(
        sender="sender-1",
        origin=ProcessingJobOrigin.YOUTUBE,
        payload={"event": "messages.upsert"},
    )

    restarted_queue = ProcessingQueue(storage_service=StorageService(database_path=database_path))
    restored_jobs = restarted_queue.list_jobs()

    assert len(restored_jobs) == 1
    assert restored_jobs[0].id == job.id
    assert restored_jobs[0].origin is ProcessingJobOrigin.YOUTUBE
    assert restarted_queue.pending_count() == 1


def test_persists_media_history(tmp_path: Path) -> None:
    database_path = tmp_path / "ykmedia.sqlite3"
    storage = StorageService(database_path=database_path)

    storage.save_media_history(
        history_id="hist-1",
        date="2026-07-27T17:00:00+00:00",
        sender="sender-1",
        origin="WhatsApp",
        category="Louvores",
        final_name="louvor.mp3",
        file_path="Louvores/louvor.mp3",
        status="CONCLUIDO",
    )

    restarted_storage = StorageService(database_path=database_path)
    history = restarted_storage.list_media_history()

    assert history == [
        {
            "id": "hist-1",
            "date": "2026-07-27T17:00:00+00:00",
            "sender": "sender-1",
            "origin": "WhatsApp",
            "category": "Louvores",
            "final_name": "louvor.mp3",
            "file_path": "Louvores/louvor.mp3",
            "status": "CONCLUIDO",
        }
    ]


def test_persists_conversation_sessions_after_restart(tmp_path: Path) -> None:
    database_path = tmp_path / "ykmedia.sqlite3"
    storage = StorageService(database_path=database_path)
    session_store = SQLiteSessionStore(storage_service=storage)
    session = ConversationSession(
        state=ConversationState.WAITING_FILENAME,
        category="Louvores",
        filename=None,
    )
    session_store.update("sender-1", session)

    restarted_store = SQLiteSessionStore(
        storage_service=StorageService(database_path=database_path)
    )
    restored_session = restarted_store.get("sender-1")

    assert restored_session is not None
    assert restored_session.state is ConversationState.WAITING_FILENAME
    assert restored_session.category == "Louvores"


def test_removes_expired_persisted_conversation_sessions(tmp_path: Path) -> None:
    database_path = tmp_path / "ykmedia.sqlite3"
    storage = StorageService(database_path=database_path)
    storage.save_session(
        sender_id="sender-1",
        state=ConversationState.WAITING_CATEGORY.value,
        category=None,
        filename=None,
        updated_at=1.0,
    )
    session_store = SQLiteSessionStore(storage_service=storage, ttl_seconds=1.0)

    removed_count = session_store.clear_expired()

    assert removed_count == 1
    assert session_store.get("sender-1") is None
