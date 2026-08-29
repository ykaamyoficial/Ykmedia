from app.models.persistence import (
    ConversationMessageDirection,
    ConversationMessageRecord,
    ConversationMessageStatus,
    MediaRecord,
    ProcessedMessageStatus,
)
from app.repositories.conversation_message_repository import (
    ConversationMessageRepository,
    InMemoryConversationMessageRepository,
)
from app.repositories.media_repository import InMemoryMediaRepository, MediaRepository
from app.repositories.processed_message_repository import (
    InMemoryProcessedMessageRepository,
    ProcessedMessageRepository,
)


def test_media_repository_contract_is_implemented() -> None:
    repository: MediaRepository = InMemoryMediaRepository()
    media = MediaRecord(
        media_id="media-1",
        message_id="MSG1",
        file_name="arquivo.jpg",
        relative_path="arquivo.jpg",
        mimetype="image/jpeg",
        size_bytes=10,
        sha256="hash",
    )

    repository.save(media)

    assert repository.exists("media-1") is True
    assert repository.get_by_id("media-1") == media
    assert repository.list() == [media]

    repository.delete("media-1")

    assert repository.exists("media-1") is False
    assert repository.get_by_id("media-1") is None
    assert repository.list() == []


def test_media_repository_returns_none_when_missing() -> None:
    repository = InMemoryMediaRepository()

    assert repository.exists("missing") is False
    assert repository.get_by_id("missing") is None
    assert repository.list() == []


def test_processed_message_repository_blocks_completed_duplicates() -> None:
    repository: ProcessedMessageRepository = InMemoryProcessedMessageRepository()

    assert repository.start("MSG1", "sender-1") is True
    repository.complete("MSG1")

    assert repository.start("MSG1", "sender-1") is False
    record = repository.get("MSG1")
    assert record is not None
    assert record.status is ProcessedMessageStatus.COMPLETED


def test_processed_message_repository_allows_retry_after_error() -> None:
    repository = InMemoryProcessedMessageRepository()

    assert repository.start("MSG1", "sender-1") is True
    repository.fail("MSG1", "download: falha")

    assert repository.start("MSG1", "sender-1") is True
    record = repository.get("MSG1")
    assert record is not None
    assert record.status is ProcessedMessageStatus.PROCESSING


def test_conversation_message_repository_contract_is_implemented() -> None:
    repository: ConversationMessageRepository = InMemoryConversationMessageRepository()
    message = ConversationMessageRecord(
        id="conv-1",
        message_id="MSG1",
        sender="sender-1",
        direction=ConversationMessageDirection.INBOUND,
        content="Ola",
        message_type="texto",
        state="WAITING_CATEGORY_SELECTION",
        media_id=None,
        created_at="2026-07-28T10:00:00+00:00",
        status=ConversationMessageStatus.RECEIVED,
    )

    repository.save(message)

    assert repository.list_by_sender("sender-1") == [message]
    contacts = repository.list_recent_contacts()
    assert contacts[0]["sender"] == "sender-1"
    assert contacts[0]["last_content"] == "Ola"
