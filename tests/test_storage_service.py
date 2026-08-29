import sqlite3
import time
from pathlib import Path

from app.models.message import MessageType, ReceivedMessage, Sender
from app.services.category_service import CategoryService
from app.services.conversation_engine import (
    ConversationEngine,
    ConversationSession,
    ConversationState,
)
from app.services.processing_queue import ProcessingJobOrigin, ProcessingQueue
from app.repositories.processed_message_repository import SQLiteProcessedMessageRepository
from app.services.session_store import SQLiteSessionStore
from app.services.storage_service import StorageService


def test_creates_database_automatically(tmp_path: Path) -> None:
    database_path = tmp_path / "ykmedia.sqlite3"

    StorageService(database_path=database_path)

    assert database_path.exists()


def test_enables_wal_and_busy_timeout(tmp_path: Path) -> None:
    database_path = tmp_path / "ykmedia.sqlite3"
    StorageService(database_path=database_path)

    with sqlite3.connect(database_path) as connection:
        journal_mode = connection.execute("PRAGMA journal_mode").fetchone()[0]

    assert journal_mode.lower() == "wal"


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


def test_lists_media_contacts_and_files_by_sender(tmp_path: Path) -> None:
    database_path = tmp_path / "ykmedia.sqlite3"
    storage = StorageService(database_path=database_path)
    storage.save_media_history(
        history_id="hist-1",
        date="2026-07-27T17:21:35+00:00",
        sender="556299999999@s.whatsapp.net",
        origin="WhatsApp",
        category="Louvores",
        final_name="louvor.mp3",
        file_path="Louvores/louvor.mp3",
        status="CONCLUIDO",
    )
    storage.save_media_history(
        history_id="hist-2",
        date="2026-07-27T18:21:35+00:00",
        sender="556299999999@s.whatsapp.net",
        origin="WhatsApp",
        category="Louvores",
        final_name="imagem.jpg",
        file_path="Louvores/imagem.jpg",
        status="CONCLUIDO",
    )

    contacts = storage.list_media_contacts()
    files = storage.list_media_by_sender("556299999999@s.whatsapp.net")

    assert contacts[0]["sender"] == "556299999999@s.whatsapp.net"
    assert contacts[0]["media_count"] == 2
    assert contacts[0]["last_media"] == "imagem.jpg"
    assert [file["final_name"] for file in files] == ["imagem.jpg", "louvor.mp3"]


def test_lists_latest_media_by_insertion_order_when_dates_match(tmp_path: Path) -> None:
    storage = StorageService(database_path=tmp_path / "ykmedia.sqlite3")
    same_date = "2026-07-29T22:42:00+00:00"

    for history_id, final_name in (
        ("hist-1", "001.mp4"),
        ("hist-2", "002.mp3"),
        ("hist-3", "003.pdf"),
    ):
        storage.save_media_history(
            history_id=history_id,
            date=same_date,
            sender="556288888888@s.whatsapp.net",
            origin="WhatsApp",
            category="Mensagens",
            final_name=final_name,
            file_path=f"Mensagens/Sessao/{final_name}",
            status="CONCLUIDO",
        )

    contacts = storage.list_media_contacts()
    files = storage.list_media_by_sender("556288888888@s.whatsapp.net")

    assert contacts[0]["last_media"] == "003.pdf"
    assert [file["final_name"] for file in files] == ["003.pdf", "002.mp3", "001.mp4"]


def test_persists_contact_profile(tmp_path: Path) -> None:
    storage = StorageService(database_path=tmp_path / "ykmedia.sqlite3")

    storage.save_contact_profile(
        sender="556299999999@s.whatsapp.net",
        display_name="Joao Silva",
        profile_picture_url="https://example.com/photo.jpg",
        profile_picture_path="data/contact_photos/556299999999.jpg",
        updated_at="2026-07-29T10:00:00+00:00",
    )

    profile = StorageService(database_path=tmp_path / "ykmedia.sqlite3").get_contact_profile(
        "556299999999@s.whatsapp.net"
    )

    assert profile is not None
    assert profile["display_name"] == "Joao Silva"
    assert profile["profile_picture_url"] == "https://example.com/photo.jpg"


def test_persists_processed_messages_after_restart(tmp_path: Path) -> None:
    database_path = tmp_path / "ykmedia.sqlite3"
    storage = StorageService(database_path=database_path)
    repository = SQLiteProcessedMessageRepository(storage_service=storage)

    assert repository.start("MSG1", "sender-1") is True
    repository.complete("MSG1")

    restarted_repository = SQLiteProcessedMessageRepository(
        storage_service=StorageService(database_path=database_path)
    )

    assert restarted_repository.start("MSG1", "sender-1") is False


def test_persists_conversation_messages_and_contacts(tmp_path: Path) -> None:
    database_path = tmp_path / "ykmedia.sqlite3"
    storage = StorageService(database_path=database_path)

    storage.save_conversation_message(
        record_id="conv-1",
        message_id="MSG1",
        sender="sender-1",
        direction="INBOUND",
        content="Ola",
        message_type="texto",
        state="WAITING_CATEGORY_SELECTION",
        media_id=None,
        created_at="2026-07-28T10:00:00+00:00",
        status="RECEBIDA",
    )
    storage.save_conversation_message(
        record_id="conv-2",
        message_id="MSG1",
        sender="sender-1",
        direction="OUTBOUND",
        content="Como deseja classifica-lo?",
        message_type="texto",
        state="WAITING_CATEGORY_SELECTION",
        media_id=None,
        created_at="2026-07-28T10:00:01+00:00",
        status="ENVIADA",
    )

    restarted_storage = StorageService(database_path=database_path)
    messages = restarted_storage.list_conversation_messages("sender-1")
    contacts = restarted_storage.list_conversation_contacts()

    assert [message["content"] for message in messages] == [
        "Ola",
        "Como deseja classifica-lo?",
    ]
    assert contacts[0]["sender"] == "sender-1"
    assert contacts[0]["last_content"] == "Como deseja classifica-lo?"
    assert contacts[0]["message_count"] == 2


def test_persists_conversation_sessions_after_restart(tmp_path: Path) -> None:
    database_path = tmp_path / "ykmedia.sqlite3"
    storage = StorageService(database_path=database_path)
    session_store = SQLiteSessionStore(storage_service=storage)
    session = ConversationSession(
        state=ConversationState.WAITING_FILENAME_DECISION,
        category="Louvores",
        filename=None,
        contact_name="Marina",
        pending_media_id="MSG1",
        allowed_option_ids=("filename:keep_original", "filename:custom"),
        processed_interaction_ids=("CLICK1",),
        interactive_created_at=123.0,
    )
    session_store.update("sender-1", session)

    restarted_store = SQLiteSessionStore(
        storage_service=StorageService(database_path=database_path)
    )
    restored_session = restarted_store.get("sender-1")

    assert restored_session is not None
    assert restored_session.state is ConversationState.WAITING_FILENAME_DECISION
    assert restored_session.category == "Louvores"
    assert restored_session.pending_media_id == "MSG1"
    assert restored_session.allowed_option_ids == (
        "filename:keep_original",
        "filename:custom",
    )
    assert restored_session.processed_interaction_ids == ("CLICK1",)
    assert restored_session.interactive_created_at == 123.0
    assert restored_session.contact_name == "Marina"


def test_adds_retry_columns_to_existing_processing_jobs_table(tmp_path: Path) -> None:
    database_path = tmp_path / "ykmedia.sqlite3"
    with sqlite3.connect(database_path) as connection:
        connection.execute(
            """
            CREATE TABLE processing_jobs (
                id TEXT PRIMARY KEY,
                sender TEXT NOT NULL,
                origin TEXT NOT NULL,
                created_at TEXT NOT NULL,
                status TEXT NOT NULL,
                payload TEXT NOT NULL,
                error TEXT
            )
            """
        )

    storage = StorageService(database_path=database_path)
    storage.save_processing_job(
        job_id="job-1",
        sender="s",
        origin="WhatsApp",
        created_at="2026-08-29T10:00:00+00:00",
        status="REPROCESSANDO",
        payload={"ok": True},
        attempts=2,
        next_attempt_at="2026-08-29T10:05:00+00:00",
    )

    row = storage.list_processing_jobs()[0]
    assert row["attempts"] == 2
    assert row["next_attempt_at"] == "2026-08-29T10:05:00+00:00"


def test_adds_pending_media_column_to_existing_database(tmp_path: Path) -> None:
    database_path = tmp_path / "ykmedia.sqlite3"
    with sqlite3.connect(database_path) as connection:
        connection.execute(
            """
            CREATE TABLE conversation_sessions (
                sender_id TEXT PRIMARY KEY,
                state TEXT NOT NULL,
                category TEXT,
                filename TEXT,
                updated_at REAL NOT NULL
            )
            """
        )

    storage = StorageService(database_path=database_path)
    session_store = SQLiteSessionStore(storage_service=storage)
    session_store.update(
        "sender-1",
        ConversationSession(
            state=ConversationState.WAITING_CATEGORY_SELECTION,
            pending_media_id="MSG1",
        ),
    )

    restored_session = session_store.get("sender-1")

    assert restored_session is not None
    assert restored_session.pending_media_id == "MSG1"


def test_sqlite_session_store_recovers_legacy_finished_state(tmp_path: Path) -> None:
    database_path = tmp_path / "ykmedia.sqlite3"
    storage = StorageService(database_path=database_path)
    storage.save_session(
        sender_id="sender-1",
        state="FINISHED",
        category=None,
        filename=None,
        pending_media_id=None,
        updated_at=time.time(),
    )
    session_store = SQLiteSessionStore(storage_service=storage)

    restored_session = session_store.get("sender-1")

    assert restored_session is not None
    assert restored_session.state is ConversationState.FINISHED


def test_conversation_engine_persists_state_changes_with_sqlite_store(tmp_path: Path) -> None:
    database_path = tmp_path / "ykmedia.sqlite3"
    storage = StorageService(database_path=database_path)
    session_store = SQLiteSessionStore(storage_service=storage)
    engine = ConversationEngine(session_store=session_store)
    message = ReceivedMessage(
        message_id="msg-1",
        sender=Sender(remote_jid="sender-1"),
        message_type=MessageType.IMAGE,
        raw_type="imageMessage",
    )

    result = engine.handle(message)

    assert result.next_state is ConversationState.WAITING_MEDIA
    persisted_session = SQLiteSessionStore(
        storage_service=StorageService(database_path=database_path)
    ).get("sender-1")
    assert persisted_session is not None
    assert persisted_session.state is ConversationState.WAITING_MEDIA


def test_removes_expired_persisted_conversation_sessions(tmp_path: Path) -> None:
    database_path = tmp_path / "ykmedia.sqlite3"
    storage = StorageService(database_path=database_path)
    storage.save_session(
        sender_id="sender-1",
        state=ConversationState.WAITING_CATEGORY_SELECTION.value,
        category=None,
        filename=None,
        pending_media_id=None,
        updated_at=1.0,
    )
    session_store = SQLiteSessionStore(storage_service=storage, ttl_seconds=1.0)

    removed_count = session_store.clear_expired()

    assert removed_count == 1
    assert session_store.get("sender-1") is None
