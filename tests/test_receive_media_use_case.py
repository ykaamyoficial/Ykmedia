import asyncio
from pathlib import Path
from typing import Any
from datetime import datetime, timedelta, timezone

from app.models.download import DownloadedMedia
from app.models.persistence import (
    ConversationMessageDirection,
    ConversationMessageRecord,
    ConversationMessageStatus,
)
from app.models.message import MessageType, ReceivedMessage
from app.repositories.conversation_message_repository import InMemoryConversationMessageRepository
from app.repositories.media_repository import InMemoryMediaRepository
from app.services.command_processor import CommandProcessor
from app.services.conversation_engine import ConversationEngine, ConversationState
from app.services.file_storage import FileStorage
from app.services.message_pipeline import MessagePipeline
from app.services.receive_media_use_case import ReceiveMediaUseCase
from app.services.session_store import MemorySessionStore
from app.services.storage_service import StorageService


class FakeDownloadManager:
    def __init__(self) -> None:
        self.calls: list[str] = []

    async def download(self, message: ReceivedMessage) -> DownloadedMedia:
        self.calls.append(message.message_id)
        suffix = {
            MessageType.IMAGE: "jpg",
            MessageType.AUDIO: "mp3",
            MessageType.VIDEO: "mp4",
            MessageType.DOCUMENT: "pdf",
        }.get(message.message_type, "bin")
        return DownloadedMedia(
            message_id=message.message_id,
            content=f"media-{message.message_id}".encode(),
            mimetype=message.media.mimetype if message.media else "application/octet-stream",
            size_bytes=len(message.message_id) + 6,
            file_name=f"{message.message_id}.{suffix}",
        )


class FakeYoutubeDownloader:
    def __init__(self) -> None:
        self.calls = 0

    def extract_url(self, text: str | None) -> str | None:
        if text and ("youtu.be" in text or "youtube.com" in text):
            return text
        return None

    async def download(self, message: ReceivedMessage) -> DownloadedMedia:
        self.calls += 1
        return DownloadedMedia(
            message_id=message.message_id,
            content=b"youtube-video",
            mimetype="video/mp4",
            size_bytes=13,
            file_name="youtube.mp4",
        )


def _payload(message: dict[str, Any], message_id: str = "MSG1", remote_jid: str = "556299999999@s.whatsapp.net") -> dict[str, Any]:
    return {
        "event": "messages.upsert",
        "data": {
            "key": {
                "id": message_id,
                "remoteJid": remote_jid,
                "fromMe": False,
            },
            "pushName": "Henrique",
            "message": message,
        },
    }


def _button_payload(option_id: str, title: str, message_id: str) -> dict[str, Any]:
    return _payload(
        {
            "buttonsResponseMessage": {
                "selectedButtonId": option_id,
                "selectedDisplayText": title,
            }
        },
        message_id,
    )


def _use_case(tmp_path: Path, youtube: FakeYoutubeDownloader | None = None) -> tuple[ReceiveMediaUseCase, InMemoryMediaRepository, ConversationEngine]:
    media_repository = InMemoryMediaRepository()
    file_storage = FileStorage(root_directory=tmp_path)
    conversation_engine = ConversationEngine(session_store=MemorySessionStore())
    pipeline = MessagePipeline(
        download_manager=FakeDownloadManager(),
        file_storage=file_storage,
        conversation_engine=conversation_engine,
        youtube_downloader=youtube,
    )
    return (
        ReceiveMediaUseCase(
            message_pipeline=pipeline,
            media_repository=media_repository,
            file_storage=file_storage,
        ),
        media_repository,
        conversation_engine,
    )


def test_text_without_active_session_is_ignored(tmp_path: Path) -> None:
    use_case, _, _ = _use_case(tmp_path)

    result = asyncio.run(use_case.execute(_payload({"conversation": "Ola"})))

    assert result.received_message is not None
    assert result.received_message.message_type is MessageType.TEXT
    assert result.stored_file is None
    assert result.conversation_state is ConversationState.IDLE
    assert result.next_message is None
    assert result.errors == []


def test_group_message_is_ignored_without_session_or_download(tmp_path: Path) -> None:
    use_case, _, _ = _use_case(tmp_path)

    result = asyncio.run(
        use_case.execute(
            _payload(
                {"imageMessage": {"mimetype": "image/jpeg"}},
                remote_jid="556299999999-123@g.us",
            )
        )
    )

    assert result.received_message is None
    assert result.next_message is None
    assert result.stored_file is None
    assert result.errors == ["mensagem_grupo"]


def test_image_starts_session_without_saving_file(tmp_path: Path) -> None:
    use_case, media_repository, engine = _use_case(tmp_path)

    result = asyncio.run(use_case.execute(_payload({"imageMessage": {"mimetype": "image/jpeg"}}, "IMG1")))

    assert result.received_message is not None
    assert result.conversation_state is ConversationState.WAITING_CATEGORY_SELECTION
    assert result.stored_file is None
    assert result.next_message is not None
    assert "Escolha a categoria" in result.next_message
    assert media_repository.list() == []
    assert list(tmp_path.rglob("*")) == []
    session = engine.get_session("556299999999@s.whatsapp.net")
    assert session is not None
    assert session.pending_media_ids == ("IMG1",)


def test_single_file_category_asks_for_rename_before_saving(tmp_path: Path) -> None:
    use_case, media_repository, engine = _use_case(tmp_path)

    asyncio.run(use_case.execute(_payload({"imageMessage": {"mimetype": "image/jpeg"}}, "IMG1")))
    result = asyncio.run(use_case.execute(_payload({"conversation": "1"}, "CAT1")))

    assert result.conversation_state is ConversationState.WAITING_FILENAME_DECISION
    assert result.stored_file is None
    assert "Deseja renomear este arquivo" in (result.next_message or "")
    assert media_repository.list() == []
    assert engine.get_session("556299999999@s.whatsapp.net") is not None


def test_single_file_keeps_original_name_after_rename_decision(tmp_path: Path) -> None:
    use_case, media_repository, engine = _use_case(tmp_path)

    asyncio.run(use_case.execute(_payload({"imageMessage": {"mimetype": "image/jpeg"}}, "IMG1")))
    asyncio.run(use_case.execute(_payload({"conversation": "1"}, "CAT1")))
    result = asyncio.run(use_case.execute(_payload({"conversation": "1"}, "NAME1")))

    assert result.conversation_state is ConversationState.FINISHED
    assert result.stored_file is not None
    assert result.stored_file.file_name == "IMG1.jpg"
    assert Path(result.stored_file.relative_path).parts[0] == "Louvores"
    assert Path(result.stored_file.absolute_path).exists()
    assert {record.file_name for record in media_repository.list()} == {"IMG1.jpg"}
    assert engine.get_session("556299999999@s.whatsapp.net") is None


def test_single_file_can_be_renamed_after_category(tmp_path: Path) -> None:
    use_case, media_repository, _ = _use_case(tmp_path)

    asyncio.run(use_case.execute(_payload({"imageMessage": {"mimetype": "image/jpeg"}}, "IMG1")))
    asyncio.run(use_case.execute(_payload({"conversation": "2"}, "CAT1")))
    ask_name = asyncio.run(use_case.execute(_payload({"conversation": "2"}, "DECIDE1")))
    result = asyncio.run(use_case.execute(_payload({"conversation": "Culto Domingo"}, "NAME1")))

    assert ask_name.conversation_state is ConversationState.WAITING_CUSTOM_FILENAME
    assert result.stored_file is not None
    assert result.stored_file.file_name == "Culto Domingo.jpg"
    assert {record.file_name for record in media_repository.list()} == {"Culto Domingo.jpg"}


def test_multiple_files_are_saved_in_received_order(tmp_path: Path) -> None:
    use_case, media_repository, _ = _use_case(tmp_path)

    asyncio.run(use_case.execute(_payload({"videoMessage": {"mimetype": "video/mp4"}}, "VID1")))
    asyncio.run(use_case.execute(_payload({"audioMessage": {"mimetype": "audio/mpeg"}}, "AUD2")))
    asyncio.run(use_case.execute(_payload({"documentMessage": {"mimetype": "application/pdf"}}, "DOC3")))
    result = asyncio.run(use_case.execute(_payload({"conversation": "2"}, "CAT1")))

    records = media_repository.list()
    assert result.stored_file is not None
    assert [record.media_id for record in records] == ["VID1", "AUD2", "DOC3"]
    assert [record.file_name for record in records] == ["001.mp4", "002.mp3", "003.pdf"]
    assert all(Path(record.absolute_path or "").exists() for record in records)
    assert all(Path(record.relative_path).parts[0] == "Mensagens" for record in records)


def test_youtube_link_uses_same_flow(tmp_path: Path) -> None:
    youtube = FakeYoutubeDownloader()
    use_case, media_repository, _ = _use_case(tmp_path, youtube=youtube)

    first_result = asyncio.run(use_case.execute(_payload({"conversation": "https://youtu.be/abc"}, "YT1")))
    category_result = asyncio.run(use_case.execute(_payload({"conversation": "3"}, "CAT1")))
    final_result = asyncio.run(use_case.execute(_payload({"conversation": "1"}, "NAME1")))

    assert youtube.calls == 1
    assert first_result.conversation_state is ConversationState.WAITING_CATEGORY_SELECTION
    assert category_result.conversation_state is ConversationState.WAITING_FILENAME_DECISION
    assert final_result.stored_file is not None
    assert media_repository.list()[0].file_name == "youtube.mp4"


def test_timeout_cancels_without_saving(tmp_path: Path) -> None:
    use_case, media_repository, engine = _use_case(tmp_path)
    asyncio.run(use_case.execute(_payload({"imageMessage": {"mimetype": "image/jpeg"}}, "IMG1")))
    session = engine.get_session("556299999999@s.whatsapp.net")
    assert session is not None
    session.expires_at = 1

    result = asyncio.run(use_case.execute(_payload({"conversation": "1"}, "CAT1")))

    assert result.next_message is not None
    assert "Nao recebemos sua resposta" in result.next_message
    assert result.stored_file is None
    assert media_repository.list() == []
    assert not any(tmp_path.rglob("*"))


def test_command_response_is_returned_as_next_message(tmp_path: Path) -> None:
    conversation_engine = ConversationEngine(session_store=MemorySessionStore())
    pipeline = MessagePipeline(
        download_manager=FakeDownloadManager(),
        file_storage=FileStorage(root_directory=tmp_path),
        conversation_engine=conversation_engine,
        command_processor=CommandProcessor(conversation_engine),
    )
    use_case = ReceiveMediaUseCase(message_pipeline=pipeline)

    result = asyncio.run(use_case.execute(_payload({"conversation": "!versao"})))

    assert result.next_message is not None
    assert result.next_message.startswith("YkMedia ")
    assert result.conversation_state is None
    assert result.stored_file is None


def test_records_media_history_after_confirmation(tmp_path: Path) -> None:
    media_repository = InMemoryMediaRepository()
    storage_service = StorageService(database_path=tmp_path / "ykmedia.sqlite3")
    file_storage = FileStorage(root_directory=tmp_path / "media")
    conversation_engine = ConversationEngine(session_store=MemorySessionStore())
    pipeline = MessagePipeline(
        download_manager=FakeDownloadManager(),
        file_storage=file_storage,
        conversation_engine=conversation_engine,
    )
    use_case = ReceiveMediaUseCase(
        message_pipeline=pipeline,
        media_repository=media_repository,
        media_history_recorder=storage_service,
        file_storage=file_storage,
    )

    asyncio.run(use_case.execute(_payload({"imageMessage": {"mimetype": "image/jpeg"}}, "IMG1")))
    asyncio.run(use_case.execute(_payload({"conversation": "1"}, "CAT1")))
    result = asyncio.run(use_case.execute(_payload({"conversation": "1"}, "NAME1")))

    history = storage_service.list_media_history()
    assert result.conversation_state is ConversationState.FINISHED
    assert len(history) == 1
    assert history[0]["sender"] == "556299999999@s.whatsapp.net"
    assert history[0]["final_name"] == "IMG1.jpg"
    assert Path(history[0]["file_path"]).parts[0] == "Louvores"


def test_records_inbound_media_conversation_message(tmp_path: Path) -> None:
    conversation_messages = InMemoryConversationMessageRepository()
    conversation_engine = ConversationEngine(session_store=MemorySessionStore())
    pipeline = MessagePipeline(
        download_manager=FakeDownloadManager(),
        file_storage=FileStorage(root_directory=tmp_path),
        conversation_engine=conversation_engine,
    )
    use_case = ReceiveMediaUseCase(
        message_pipeline=pipeline,
        conversation_message_repository=conversation_messages,
    )

    result = asyncio.run(use_case.execute(_payload({"imageMessage": {"mimetype": "image/jpeg"}}, "IMG1")))
    messages = conversation_messages.list_by_sender("556299999999@s.whatsapp.net")

    assert result.next_message is not None
    assert len(messages) == 1
    assert messages[0].message_type == "imagem"
    assert messages[0].state == ConversationState.WAITING_CATEGORY_SELECTION.value


def test_text_after_one_day_receives_usage_info(tmp_path: Path) -> None:
    conversation_messages = InMemoryConversationMessageRepository()
    old_date = datetime.now(timezone.utc) - timedelta(days=1, minutes=1)
    conversation_messages.save(
        ConversationMessageRecord(
            id="old",
            message_id="OLD",
            sender="556299999999@s.whatsapp.net",
            direction=ConversationMessageDirection.INBOUND,
            content="Oi",
            message_type="texto",
            state=ConversationState.IDLE.value,
            media_id=None,
            created_at=old_date.isoformat(timespec="seconds"),
            status=ConversationMessageStatus.RECEIVED,
        )
    )
    conversation_engine = ConversationEngine(session_store=MemorySessionStore())
    pipeline = MessagePipeline(
        download_manager=FakeDownloadManager(),
        file_storage=FileStorage(root_directory=tmp_path),
        conversation_engine=conversation_engine,
    )
    use_case = ReceiveMediaUseCase(
        message_pipeline=pipeline,
        conversation_message_repository=conversation_messages,
    )

    result = asyncio.run(use_case.execute(_payload({"conversation": "Oi"})))

    assert result.next_message is not None
    assert "resposta automatica da equipe de Sonoplastia" in result.next_message


def test_text_before_one_day_stays_silent(tmp_path: Path) -> None:
    conversation_messages = InMemoryConversationMessageRepository()
    recent_date = datetime.now(timezone.utc) - timedelta(hours=2)
    conversation_messages.save(
        ConversationMessageRecord(
            id="recent",
            message_id="RECENT",
            sender="556299999999@s.whatsapp.net",
            direction=ConversationMessageDirection.INBOUND,
            content="Oi",
            message_type="texto",
            state=ConversationState.IDLE.value,
            media_id=None,
            created_at=recent_date.isoformat(timespec="seconds"),
            status=ConversationMessageStatus.RECEIVED,
        )
    )
    conversation_engine = ConversationEngine(session_store=MemorySessionStore())
    pipeline = MessagePipeline(
        download_manager=FakeDownloadManager(),
        file_storage=FileStorage(root_directory=tmp_path),
        conversation_engine=conversation_engine,
    )
    use_case = ReceiveMediaUseCase(
        message_pipeline=pipeline,
        conversation_message_repository=conversation_messages,
    )

    result = asyncio.run(use_case.execute(_payload({"conversation": "Oi"})))

    assert result.next_message is None
