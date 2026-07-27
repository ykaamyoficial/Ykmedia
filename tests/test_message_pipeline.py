import asyncio
from typing import Any

import pytest

from app.models.download import DownloadedMedia
from app.models.message import Media, MessageType, ReceivedMessage, Sender
from app.models.storage import StoredFile
from app.services.command_processor import CommandProcessor
from app.services.conversation_engine import ConversationEngine, ConversationState
from app.services.evolution_message_mapper import map_evolution_payload
from app.services.file_storage import FileWriteError
from app.services.message_pipeline import MessagePipeline
from app.services.session_store import MemorySessionStore


class FakeDownloadManager:
    def __init__(self, result: DownloadedMedia | Exception) -> None:
        self.result = result
        self.calls = 0

    async def download(self, message: ReceivedMessage) -> DownloadedMedia:
        self.calls += 1
        if isinstance(self.result, Exception):
            raise self.result

        return self.result


class FakeFileStorage:
    def __init__(self, result: StoredFile | Exception) -> None:
        self.result = result
        self.calls = 0

    def save(self, media: DownloadedMedia) -> StoredFile:
        self.calls += 1
        if isinstance(self.result, Exception):
            raise self.result

        return self.result


class FakeYoutubeDownloader:
    def __init__(self, result: DownloadedMedia | Exception) -> None:
        self.result = result
        self.calls = 0

    def extract_url(self, text: str | None) -> str | None:
        if text and "youtube.com" in text:
            return "https://www.youtube.com/watch?v=abc"

        if text and "youtu.be" in text:
            return "https://youtu.be/abc"

        return None

    async def download(self, message: ReceivedMessage) -> DownloadedMedia:
        self.calls += 1
        if isinstance(self.result, Exception):
            raise self.result

        return self.result


def _payload(message: dict[str, Any]) -> dict[str, Any]:
    return {
        "event": "messages.upsert",
        "data": {
            "key": {
                "id": "MSG1",
                "remoteJid": "556299999999@s.whatsapp.net",
                "fromMe": False,
            },
            "message": message,
        },
    }


def _downloaded_media() -> DownloadedMedia:
    return DownloadedMedia(
        message_id="MSG1",
        content=b"audio",
        mimetype="audio/ogg",
        size_bytes=5,
        file_name="audio.ogg",
    )


def _stored_file() -> StoredFile:
    return StoredFile(
        absolute_path="C:\\media\\audio.ogg",
        relative_path="audio.ogg",
        file_name="audio.ogg",
        extension=".ogg",
        size_bytes=5,
        sha256="hash",
    )


def _pipeline(
    download_result: DownloadedMedia | Exception | None = None,
    storage_result: StoredFile | Exception | None = None,
) -> tuple[MessagePipeline, FakeDownloadManager, FakeFileStorage]:
    download_manager = FakeDownloadManager(download_result or _downloaded_media())
    file_storage = FakeFileStorage(storage_result or _stored_file())
    pipeline = MessagePipeline(
        download_manager=download_manager,
        file_storage=file_storage,
        conversation_engine=ConversationEngine(session_store=MemorySessionStore()),
    )
    return pipeline, download_manager, file_storage


class SpyConversationEngine:
    def __init__(self) -> None:
        self.calls = 0
        self._engine = ConversationEngine(session_store=MemorySessionStore())

    def handle(self, message: ReceivedMessage):
        self.calls += 1
        return self._engine.handle(message)

    def get_session(self, remote_jid: str):
        return self._engine.get_session(remote_jid)

    def reset(self, remote_jid: str) -> None:
        self._engine.reset(remote_jid)


def test_processes_text_message_without_download_or_storage() -> None:
    pipeline, download_manager, file_storage = _pipeline()

    result = asyncio.run(pipeline.process_event(_payload({"conversation": "Ola"})))

    assert result.received_message is not None
    assert result.received_message.message_type is MessageType.TEXT
    assert result.processing_decision is not None
    assert result.downloaded_media is None
    assert result.stored_file is None
    assert result.conversation_result is not None
    assert result.conversation_result.next_state is ConversationState.WAITING_CATEGORY
    assert result.errors == []
    assert download_manager.calls == 0
    assert file_storage.calls == 0


def test_processes_media_message_with_download_and_storage() -> None:
    downloaded_media = _downloaded_media()
    stored_file = _stored_file()
    pipeline, download_manager, file_storage = _pipeline(
        download_result=downloaded_media,
        storage_result=stored_file,
    )

    result = asyncio.run(
        pipeline.process_event(_payload({"audioMessage": {"mimetype": "audio/ogg"}}))
    )

    assert result.received_message is not None
    assert result.received_message.media is not None
    assert result.downloaded_media == downloaded_media
    assert result.stored_file == stored_file
    assert result.conversation_result is not None
    assert result.errors == []
    assert download_manager.calls == 1
    assert file_storage.calls == 1


def test_returns_error_for_invalid_message() -> None:
    pipeline, download_manager, file_storage = _pipeline()

    result = asyncio.run(pipeline.process_event({"event": "messages.upsert", "data": None}))

    assert result.received_message is None
    assert result.processing_decision is None
    assert result.downloaded_media is None
    assert result.stored_file is None
    assert result.conversation_result is None
    assert result.errors == ["mensagem_invalida"]
    assert download_manager.calls == 0
    assert file_storage.calls == 0


def test_records_download_failure_and_continues_to_conversation() -> None:
    pipeline, download_manager, file_storage = _pipeline(download_result=RuntimeError("falha download"))

    result = asyncio.run(
        pipeline.process_event(_payload({"audioMessage": {"mimetype": "audio/ogg"}}))
    )

    assert result.received_message is not None
    assert result.downloaded_media is None
    assert result.stored_file is None
    assert result.conversation_result is not None
    assert result.errors == ["download: falha download"]
    assert download_manager.calls == 1
    assert file_storage.calls == 0


def test_records_storage_failure_and_continues_to_conversation() -> None:
    downloaded_media = _downloaded_media()
    pipeline, download_manager, file_storage = _pipeline(
        download_result=downloaded_media,
        storage_result=FileWriteError("falha storage"),
    )

    result = asyncio.run(
        pipeline.process_event(_payload({"audioMessage": {"mimetype": "audio/ogg"}}))
    )

    assert result.downloaded_media == downloaded_media
    assert result.stored_file is None
    assert result.conversation_result is not None
    assert result.errors == ["storage: falha storage"]
    assert download_manager.calls == 1
    assert file_storage.calls == 1


def test_full_flow_without_errors() -> None:
    pipeline, _, _ = _pipeline()

    result = asyncio.run(
        pipeline.process_event(_payload({"documentMessage": {"mimetype": "application/pdf"}}))
    )

    assert result.received_message is not None
    assert result.processing_decision is not None
    assert result.downloaded_media is not None
    assert result.stored_file is not None
    assert result.conversation_result is not None
    assert result.errors == []


def test_pipeline_uses_payload_mapper() -> None:
    result = map_evolution_payload(_payload({"conversation": "Ola"}))

    assert result.message is not None
    assert result.message.sender == Sender(remote_jid="556299999999@s.whatsapp.net")


def test_command_message_does_not_enter_conversation_engine() -> None:
    conversation_engine = SpyConversationEngine()
    pipeline = MessagePipeline(
        download_manager=FakeDownloadManager(_downloaded_media()),
        file_storage=FakeFileStorage(_stored_file()),
        conversation_engine=conversation_engine,
        command_processor=CommandProcessor(conversation_engine._engine),
    )

    result = asyncio.run(pipeline.process_event(_payload({"conversation": "!ajuda"})))

    assert result.command_result is not None
    assert "!status" in result.command_result.response
    assert result.conversation_result is None
    assert conversation_engine.calls == 0


def test_youtube_link_reuses_media_storage_flow() -> None:
    downloaded_media = DownloadedMedia(
        message_id="MSG1",
        content=b"video",
        mimetype="video/mp4",
        size_bytes=5,
        file_name="youtube.mp4",
    )
    youtube_downloader = FakeYoutubeDownloader(downloaded_media)
    file_storage = FakeFileStorage(_stored_file())
    pipeline = MessagePipeline(
        download_manager=FakeDownloadManager(_downloaded_media()),
        file_storage=file_storage,
        conversation_engine=ConversationEngine(session_store=MemorySessionStore()),
        youtube_downloader=youtube_downloader,
    )

    result = asyncio.run(
        pipeline.process_event(_payload({"conversation": "https://www.youtube.com/watch?v=abc"}))
    )

    assert result.downloaded_media == downloaded_media
    assert result.stored_file == _stored_file()
    assert result.conversation_result is not None
    assert youtube_downloader.calls == 1
    assert file_storage.calls == 1
