from app.models.persistence import ConversationRecord, MediaRecord
from app.repositories.conversation_repository import (
    ConversationRepository,
    InMemoryConversationRepository,
)
from app.repositories.media_repository import InMemoryMediaRepository, MediaRepository
from app.services.conversation_engine import ConversationState


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


def test_media_repository_returns_none_when_missing() -> None:
    repository = InMemoryMediaRepository()

    assert repository.exists("missing") is False
    assert repository.get_by_id("missing") is None
    assert repository.list() == []


def test_conversation_repository_contract_is_implemented() -> None:
    repository: ConversationRepository = InMemoryConversationRepository()
    conversation = ConversationRecord(
        sender_id="sender-1",
        state=ConversationState.WAITING_CATEGORY,
    )

    repository.save(conversation)

    assert repository.get("sender-1") == conversation
    assert repository.list_active() == [conversation]


def test_conversation_repository_delete() -> None:
    repository = InMemoryConversationRepository()
    conversation = ConversationRecord(
        sender_id="sender-1",
        state=ConversationState.WAITING_CATEGORY,
    )
    repository.save(conversation)

    repository.delete("sender-1")

    assert repository.get("sender-1") is None
    assert repository.list_active() == []


def test_conversation_repository_lists_only_active_records() -> None:
    repository = InMemoryConversationRepository()
    active = ConversationRecord(
        sender_id="sender-1",
        state=ConversationState.WAITING_CATEGORY,
        is_active=True,
    )
    inactive = ConversationRecord(
        sender_id="sender-2",
        state=ConversationState.FINISHED,
        is_active=False,
    )

    repository.save(active)
    repository.save(inactive)

    assert repository.list_active() == [active]
