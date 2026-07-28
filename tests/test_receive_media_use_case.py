import asyncio
from pathlib import Path
from typing import Any

from app.models.download import DownloadedMedia
from app.models.message import MessageType, ReceivedMessage
from app.models.storage import StoredFile
from app.repositories.media_repository import InMemoryMediaRepository
from app.services.command_processor import CommandProcessor
from app.services.conversation_engine import ConversationEngine, ConversationState
from app.services.file_storage import FileStorage, FileWriteError
from app.services.message_pipeline import MessagePipeline
from app.services.receive_media_use_case import ReceiveMediaUseCase
from app.services.session_store import MemorySessionStore


class FakeDownloadManager:
    def __init__(self, result: DownloadedMedia | Exception) -> None:
        self.result = result

    async def download(self, message: ReceivedMessage) -> DownloadedMedia:
        if isinstance(self.result, Exception):
            raise self.result

        return self.result


class FakeFileStorage:
    def __init__(self, result: StoredFile | Exception) -> None:
        self.result = result

    def save(self, media: DownloadedMedia) -> StoredFile:
        if isinstance(self.result, Exception):
            raise self.result

        return self.result


class FakeYoutubeDownloader:
    def __init__(self, result: DownloadedMedia) -> None:
        self.result = result

    def extract_url(self, text: str | None) -> str | None:
        if text and "youtu.be" in text:
            return "https://youtu.be/abc"

        return None

    async def download(self, message: ReceivedMessage) -> DownloadedMedia:
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


def _downloaded_media(mimetype: str = "image/jpeg") -> DownloadedMedia:
    return DownloadedMedia(
        message_id="MSG1",
        content=b"media",
        mimetype=mimetype,
        size_bytes=5,
        file_name="media.bin",
    )


def _stored_file() -> StoredFile:
    return StoredFile(
        absolute_path="C:\\media\\media.bin",
        relative_path="media.bin",
        file_name="media.bin",
        extension=".bin",
        size_bytes=5,
        sha256="hash",
    )


def _use_case(
    download_result: DownloadedMedia | Exception | None = None,
    storage_result: StoredFile | Exception | None = None,
) -> ReceiveMediaUseCase:
    file_storage = FakeFileStorage(storage_result or _stored_file())
    pipeline = MessagePipeline(
        download_manager=FakeDownloadManager(download_result or _downloaded_media()),
        file_storage=file_storage,
        conversation_engine=ConversationEngine(session_store=MemorySessionStore()),
    )
    return ReceiveMediaUseCase(pipeline, file_storage=file_storage)  # type: ignore[arg-type]


def test_receives_image() -> None:
    use_case = _use_case(_downloaded_media("image/jpeg"), _stored_file())

    result = asyncio.run(use_case.execute(_payload({"imageMessage": {"mimetype": "image/jpeg"}})))

    assert result.received_message is not None
    assert result.received_message.message_type is MessageType.IMAGE
    assert result.stored_file is None
    assert result.conversation_state is ConversationState.WAITING_USAGE_CONFIRMATION
    assert result.next_message is not None
    assert "sonoplastia" in result.next_message
    assert result.errors == []


def test_receives_audio() -> None:
    use_case = _use_case(_downloaded_media("audio/ogg"), _stored_file())

    result = asyncio.run(use_case.execute(_payload({"audioMessage": {"mimetype": "audio/ogg"}})))

    assert result.received_message is not None
    assert result.received_message.message_type is MessageType.AUDIO
    assert result.stored_file is None
    assert result.errors == []


def test_receives_video() -> None:
    use_case = _use_case(_downloaded_media("video/mp4"), _stored_file())

    result = asyncio.run(use_case.execute(_payload({"videoMessage": {"mimetype": "video/mp4"}})))

    assert result.received_message is not None
    assert result.received_message.message_type is MessageType.VIDEO
    assert result.stored_file is None
    assert result.errors == []


def test_receives_document() -> None:
    use_case = _use_case(_downloaded_media("application/pdf"), _stored_file())

    result = asyncio.run(
        use_case.execute(_payload({"documentMessage": {"mimetype": "application/pdf"}}))
    )

    assert result.received_message is not None
    assert result.received_message.message_type is MessageType.DOCUMENT
    assert result.stored_file is None
    assert result.errors == []


def test_receives_text_without_file() -> None:
    use_case = _use_case()

    result = asyncio.run(use_case.execute(_payload({"conversation": "Ola"})))

    assert result.received_message is not None
    assert result.received_message.message_type is MessageType.TEXT
    assert result.stored_file is None
    assert result.conversation_state is ConversationState.WAITING_USAGE_CONFIRMATION
    assert result.next_message is not None
    assert result.errors == []


def test_reports_download_failure() -> None:
    use_case = _use_case(download_result=RuntimeError("falha download"))

    result = asyncio.run(use_case.execute(_payload({"imageMessage": {"mimetype": "image/jpeg"}})))

    assert result.received_message is not None
    assert result.stored_file is None
    assert result.conversation_state is ConversationState.WAITING_USAGE_CONFIRMATION
    assert result.errors == ["download: falha download"]


def test_reports_storage_failure_after_usage_confirmation() -> None:
    use_case = _use_case(
        download_result=_downloaded_media("image/jpeg"),
        storage_result=FileWriteError("falha gravacao"),
    )

    asyncio.run(use_case.execute(_payload({"imageMessage": {"mimetype": "image/jpeg"}})))
    result = asyncio.run(use_case.execute(_payload({"conversation": "1"})))

    assert result.received_message is not None
    assert result.stored_file is None
    assert result.conversation_state is ConversationState.WAITING_CATEGORY
    assert result.errors == ["storage: falha gravacao"]


def test_reports_invalid_payload() -> None:
    use_case = _use_case()

    result = asyncio.run(use_case.execute({"event": "messages.upsert", "data": None}))

    assert result.received_message is None
    assert result.stored_file is None
    assert result.conversation_state is None
    assert result.next_message is None
    assert result.errors == ["mensagem_invalida"]


def test_complete_conversation_flow_renames_saved_image(tmp_path: Path) -> None:
    media_repository = InMemoryMediaRepository()
    file_storage = FileStorage(root_directory=tmp_path)
    conversation_engine = ConversationEngine(session_store=MemorySessionStore())
    pipeline = MessagePipeline(
        download_manager=FakeDownloadManager(_downloaded_media("image/jpeg")),
        file_storage=file_storage,
        conversation_engine=conversation_engine,
    )
    use_case = ReceiveMediaUseCase(
        message_pipeline=pipeline,
        media_repository=media_repository,
        file_storage=file_storage,
    )

    first_result = asyncio.run(
        use_case.execute(_payload({"imageMessage": {"mimetype": "image/jpeg"}}))
    )
    confirmation_result = asyncio.run(use_case.execute(_payload({"conversation": "1"})))
    category_result = asyncio.run(use_case.execute(_payload({"conversation": "3"})))
    filename_result = asyncio.run(use_case.execute(_payload({"conversation": "foto_culto"})))

    assert first_result.conversation_state is ConversationState.WAITING_USAGE_CONFIRMATION
    assert first_result.stored_file is None
    assert confirmation_result.conversation_state is ConversationState.WAITING_CATEGORY
    assert confirmation_result.stored_file is not None
    assert category_result.conversation_state is ConversationState.WAITING_FILENAME
    assert filename_result.conversation_state is ConversationState.FINISHED
    assert filename_result.stored_file is not None
    assert filename_result.stored_file.file_name == "foto_culto.bin"
    assert Path(filename_result.stored_file.relative_path) == Path("Jovens") / "foto_culto.bin"
    assert Path(filename_result.stored_file.absolute_path).exists()
    assert not (tmp_path / "media.bin").exists()
    assert filename_result.errors == []


def test_category_defines_destination_folder_automatically(tmp_path: Path) -> None:
    media_repository = InMemoryMediaRepository()
    file_storage = FileStorage(root_directory=tmp_path)
    conversation_engine = ConversationEngine(session_store=MemorySessionStore())
    pipeline = MessagePipeline(
        download_manager=FakeDownloadManager(_downloaded_media("image/jpeg")),
        file_storage=file_storage,
        conversation_engine=conversation_engine,
    )
    use_case = ReceiveMediaUseCase(
        message_pipeline=pipeline,
        media_repository=media_repository,
        file_storage=file_storage,
    )

    asyncio.run(use_case.execute(_payload({"imageMessage": {"mimetype": "image/jpeg"}})))
    asyncio.run(use_case.execute(_payload({"conversation": "1"})))
    asyncio.run(use_case.execute(_payload({"conversation": "1"})))
    result = asyncio.run(use_case.execute(_payload({"conversation": "louvor_especial"})))

    assert result.stored_file is not None
    assert Path(result.stored_file.relative_path) == Path("Louvores") / "louvor_especial.bin"
    assert Path(result.stored_file.absolute_path).exists()


def test_command_response_is_returned_as_next_message() -> None:
    conversation_engine = ConversationEngine(session_store=MemorySessionStore())
    pipeline = MessagePipeline(
        download_manager=FakeDownloadManager(_downloaded_media()),
        file_storage=FakeFileStorage(_stored_file()),
        conversation_engine=conversation_engine,
        command_processor=CommandProcessor(conversation_engine),
    )
    use_case = ReceiveMediaUseCase(message_pipeline=pipeline)

    result = asyncio.run(use_case.execute(_payload({"conversation": "!versao"})))

    assert result.next_message is not None
    assert result.next_message.startswith("YkMedia ")
    assert result.conversation_state is None
    assert result.stored_file is None


def test_youtube_complete_flow_reuses_existing_media_flow(tmp_path: Path) -> None:
    media_repository = InMemoryMediaRepository()
    file_storage = FileStorage(root_directory=tmp_path)
    conversation_engine = ConversationEngine(session_store=MemorySessionStore())
    pipeline = MessagePipeline(
        download_manager=FakeDownloadManager(_downloaded_media()),
        file_storage=file_storage,
        conversation_engine=conversation_engine,
        youtube_downloader=FakeYoutubeDownloader(_downloaded_media("video/mp4")),
    )
    use_case = ReceiveMediaUseCase(
        message_pipeline=pipeline,
        media_repository=media_repository,
        file_storage=file_storage,
    )

    first_result = asyncio.run(use_case.execute(_payload({"conversation": "https://youtu.be/abc"})))
    confirmation_result = asyncio.run(use_case.execute(_payload({"conversation": "1"})))
    category_result = asyncio.run(use_case.execute(_payload({"conversation": "3"})))
    filename_result = asyncio.run(use_case.execute(_payload({"conversation": "video_culto"})))

    assert first_result.conversation_state is ConversationState.WAITING_USAGE_CONFIRMATION
    assert confirmation_result.conversation_state is ConversationState.WAITING_CATEGORY
    assert category_result.conversation_state is ConversationState.WAITING_FILENAME
    assert filename_result.conversation_state is ConversationState.FINISHED
    assert filename_result.stored_file is not None
    assert Path(filename_result.stored_file.relative_path) == Path("Jovens") / "video_culto.bin"
    assert filename_result.errors == []


def test_does_not_report_success_when_pending_file_is_missing() -> None:
    media_repository = InMemoryMediaRepository()
    file_storage = FileStorage()
    conversation_engine = ConversationEngine(session_store=MemorySessionStore())
    pipeline = MessagePipeline(
        download_manager=FakeDownloadManager(_downloaded_media("image/jpeg")),
        file_storage=file_storage,
        conversation_engine=conversation_engine,
    )
    use_case = ReceiveMediaUseCase(
        message_pipeline=pipeline,
        media_repository=media_repository,
        file_storage=file_storage,
    )

    asyncio.run(use_case.execute(_payload({"conversation": "texto sem arquivo"})))
    result = asyncio.run(use_case.execute(_payload({"conversation": "1"})))

    assert result.stored_file is None
    assert result.errors == ["storage: arquivo pendente nao encontrado para confirmar."]
    assert result.next_message is not None
    assert "Envie o arquivo novamente" in result.next_message
