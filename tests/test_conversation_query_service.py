from pathlib import Path

import pytest

from app.services.conversation_query_service import ConversationNotFoundError, ConversationQueryService
from app.services.storage_service import StorageService


def _storage(tmp_path: Path) -> StorageService:
    return StorageService(database_path=tmp_path / "ykmedia.sqlite3")


def _message(
    storage: StorageService,
    record_id: str,
    sender: str,
    content: str,
    created_at: str,
    direction: str = "INBOUND",
) -> None:
    storage.save_conversation_message(
        record_id=record_id,
        message_id=record_id,
        sender=sender,
        direction=direction,
        content=content,
        message_type="text",
        state=None,
        media_id=None,
        created_at=created_at,
        status="RECEBIDA",
    )


def test_list_conversations_is_paginated_and_ordered_by_recent_activity(tmp_path: Path) -> None:
    storage = _storage(tmp_path)
    _message(storage, "msg-1", "5562999999999@s.whatsapp.net", "primeira", "2026-07-29T10:00:00+00:00")
    _message(storage, "msg-2", "5562988888888@s.whatsapp.net", "mais recente", "2026-07-29T11:00:00+00:00")

    response = ConversationQueryService(storage).list_conversations(page=1, page_size=1)

    assert response.total == 2
    assert response.has_next is True
    assert response.items[0].phone == "(62) 98888-8888"
    assert response.items[0].last_message_preview == "mais recente"


def test_search_uses_saved_display_name(tmp_path: Path) -> None:
    storage = _storage(tmp_path)
    sender = "5562777777777@s.whatsapp.net"
    _message(storage, "msg-1", sender, "ola", "2026-07-29T10:00:00+00:00")
    storage.save_contact_profile(sender=sender, display_name="Joao Silva")

    response = ConversationQueryService(storage).list_conversations(search="joao")

    assert response.total == 1
    assert response.items[0].display_name == "Joao Silva"


def test_name_falls_back_to_formatted_phone(tmp_path: Path) -> None:
    storage = _storage(tmp_path)
    _message(storage, "msg-1", "556233334444@s.whatsapp.net", "ola", "2026-07-29T10:00:00+00:00")

    item = ConversationQueryService(storage).list_conversations().items[0]

    assert item.display_name == "(62) 3333-4444"
    assert item.contact_id == "556233334444@s.whatsapp.net"


def test_get_conversation_returns_details_and_profile_photo_without_requiring_file(tmp_path: Path) -> None:
    storage = _storage(tmp_path)
    sender = "5562999999999@s.whatsapp.net"
    _message(storage, "msg-1", sender, "ola", "2026-07-29T10:00:00+00:00")
    storage.save_contact_profile(
        sender=sender,
        display_name="Maria",
        profile_picture_url="https://example.com/maria.jpg",
        profile_picture_path=str(tmp_path / "missing.jpg"),
    )

    conversation = ConversationQueryService(storage).list_conversations().items[0]
    details = ConversationQueryService(storage).get_conversation(conversation.id)

    assert details.profile.display_name == "Maria"
    assert details.profile.profile_photo_url == "https://example.com/maria.jpg"
    assert details.message_count == 1


def test_list_messages_returns_recent_page_in_visual_chronological_order(tmp_path: Path) -> None:
    storage = _storage(tmp_path)
    sender = "5562999999999@s.whatsapp.net"
    _message(storage, "msg-1", sender, "antiga", "2026-07-29T10:00:00+00:00")
    _message(storage, "msg-2", sender, "recente", "2026-07-29T11:00:00+00:00", direction="OUTBOUND")
    conversation = ConversationQueryService(storage).list_conversations().items[0]

    response = ConversationQueryService(storage).list_messages(conversation.id, page=1, page_size=2)

    assert [item.content for item in response.items] == ["antiga", "recente"]
    assert response.items[1].direction == "OUTBOUND"


def test_list_messages_exposes_saved_media_history_for_file_workspace(tmp_path: Path) -> None:
    storage = _storage(tmp_path)
    sender = "5562999999999@s.whatsapp.net"
    _message(storage, "msg-1", sender, "Mensagem recebida: imagem", "2026-07-29T10:00:00+00:00")
    media_file = tmp_path / "media" / "Louvores" / "foto.jpg"
    media_file.parent.mkdir(parents=True)
    media_file.write_bytes(b"image")
    storage.save_media_history(
        history_id="history-1",
        date="2026-07-29T10:05:00+00:00",
        sender=sender,
        origin="WhatsApp",
        category="Louvores",
        final_name="foto.jpg",
        file_path=str(media_file),
        status="CONCLUIDO",
    )
    conversation = ConversationQueryService(storage).list_conversations().items[0]

    response = ConversationQueryService(storage).list_messages(conversation.id)
    media_item = next(item for item in response.items if item.id == "media-history-history-1")

    assert media_item.content == "foto.jpg"
    assert media_item.media_metadata is not None
    assert media_item.media_metadata["final_name"] == "foto.jpg"
    assert media_item.media_metadata["absolute_path"] == str(media_file)
    assert media_item.media_metadata["size"] == 5
    assert media_item.media_metadata["exists"] is True


def test_missing_conversation_raises_not_found(tmp_path: Path) -> None:
    service = ConversationQueryService(_storage(tmp_path))

    with pytest.raises(ConversationNotFoundError):
        service.get_conversation("nao-existe")


def test_empty_endpoint_shape_has_no_items(tmp_path: Path) -> None:
    response = ConversationQueryService(_storage(tmp_path)).list_conversations()

    assert response.total == 0
    assert response.items == []
    assert response.has_next is False
