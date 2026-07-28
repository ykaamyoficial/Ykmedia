from dataclasses import dataclass, field
from typing import Any

from app.models.download import DownloadedMedia
from app.models.persistence import MediaRecord
from app.models.message import ReceivedMessage
from app.models.storage import StoredFile
from app.repositories.conversation_repository import ConversationRepository
from app.repositories.media_repository import MediaRepository
from app.services.conversation_engine import ConversationState
from app.services.file_storage import FileStorage, FileStorageError
from app.services.message_pipeline import MessagePipeline


@dataclass(frozen=True, slots=True)
class ReceiveMediaResult:
    received_message: ReceivedMessage | None
    stored_file: StoredFile | None
    conversation_state: ConversationState | None
    next_message: str | None
    errors: list[str] = field(default_factory=list)


class ReceiveMediaUseCase:
    def __init__(
        self,
        message_pipeline: MessagePipeline,
        media_repository: MediaRepository | None = None,
        conversation_repository: ConversationRepository | None = None,
        file_storage: FileStorage | None = None,
    ) -> None:
        self._message_pipeline = message_pipeline
        self._media_repository = media_repository
        self._conversation_repository = conversation_repository
        self._file_storage = file_storage
        self._pending_downloads: dict[str, DownloadedMedia] = {}

    async def execute(self, payload: dict[str, Any]) -> ReceiveMediaResult:
        pipeline_result = await self._message_pipeline.process_event(payload)
        conversation_result = pipeline_result.conversation_result
        command_result = pipeline_result.command_result
        received_message = pipeline_result.received_message
        stored_file = pipeline_result.stored_file
        errors = list(pipeline_result.errors)
        next_message_override: str | None = None

        if received_message is not None and pipeline_result.downloaded_media is not None:
            self._pending_downloads[received_message.sender.remote_jid] = (
                pipeline_result.downloaded_media
            )

        if (
            received_message is not None
            and conversation_result is not None
            and conversation_result.current_state is ConversationState.WAITING_USAGE_CONFIRMATION
            and conversation_result.next_state is ConversationState.WAITING_CATEGORY
        ):
            try:
                stored_file = self._store_confirmed_media(received_message)
            except FileStorageError as exc:
                errors.append(f"storage: {exc}")
            else:
                if stored_file is None:
                    errors.append("storage: arquivo pendente nao encontrado para confirmar.")
                    next_message_override = (
                        "Nao encontrei o arquivo pendente para confirmar. "
                        "Envie o arquivo novamente para iniciar um novo processo."
                    )
                    self._message_pipeline.conversation_engine.reset(
                        received_message.sender.remote_jid
                    )

        if (
            received_message is not None
            and conversation_result is not None
            and conversation_result.current_state is ConversationState.WAITING_USAGE_CONFIRMATION
            and conversation_result.next_state is ConversationState.FINISHED
        ):
            self._pending_downloads.pop(received_message.sender.remote_jid, None)

        if (
            received_message is not None
            and conversation_result is not None
            and conversation_result.current_state is ConversationState.WAITING_FILENAME
            and conversation_result.next_state is ConversationState.FINISHED
        ):
            try:
                renamed_file = self._move_pending_media(received_message)
            except FileStorageError as exc:
                errors.append(f"storage: {exc}")
            else:
                if renamed_file is not None:
                    stored_file = renamed_file
                else:
                    errors.append("storage: arquivo pendente nao encontrado para finalizar.")
                    next_message_override = (
                        "Nao encontrei o arquivo pendente para finalizar. "
                        "Envie o arquivo novamente para iniciar um novo processo."
                    )
                    self._message_pipeline.conversation_engine.reset(
                        received_message.sender.remote_jid
                    )

        return ReceiveMediaResult(
            received_message=received_message,
            stored_file=stored_file,
            conversation_state=(
                conversation_result.next_state if conversation_result is not None else None
            ),
            next_message=(
                next_message_override
                if next_message_override is not None
                else command_result.response
                if command_result is not None
                else conversation_result.suggested_response
                if conversation_result is not None
                else None
            ),
            errors=errors,
        )

    def _save_pending_media(
        self,
        message: ReceivedMessage,
        stored_file: StoredFile,
        mimetype: str | None,
    ) -> None:
        if self._media_repository is None:
            return

        self._media_repository.save(
            MediaRecord(
                media_id=message.sender.remote_jid,
                message_id=message.message_id,
                file_name=stored_file.file_name,
                relative_path=stored_file.relative_path,
                mimetype=mimetype,
                size_bytes=stored_file.size_bytes,
                sha256=stored_file.sha256,
                absolute_path=stored_file.absolute_path,
            )
        )

    def _store_confirmed_media(self, message: ReceivedMessage) -> StoredFile | None:
        if self._file_storage is None:
            return None

        downloaded_media = self._pending_downloads.get(message.sender.remote_jid)
        if downloaded_media is None:
            return None

        stored_file = self._file_storage.save(downloaded_media)
        self._save_pending_media(
            message=message,
            stored_file=stored_file,
            mimetype=downloaded_media.mimetype,
        )
        return stored_file

    def _move_pending_media(self, message: ReceivedMessage) -> StoredFile | None:
        if self._media_repository is None or self._file_storage is None:
            return None

        media_record = self._media_repository.get_by_id(message.sender.remote_jid)
        if media_record is None or media_record.absolute_path is None:
            return None

        session = self._message_pipeline.conversation_engine.get_session(message.sender.remote_jid)
        if session is None or not session.filename or not session.category:
            return None

        stored_file = StoredFile(
            absolute_path=media_record.absolute_path,
            relative_path=media_record.relative_path,
            file_name=media_record.file_name,
            extension=f".{media_record.file_name.rsplit('.', 1)[1]}"
            if "." in media_record.file_name
            else "",
            size_bytes=media_record.size_bytes,
            sha256=media_record.sha256,
        )
        renamed_file = self._file_storage.move(
            stored_file=stored_file,
            destination_folder=session.category,
            new_file_name=session.filename,
        )
        self._media_repository.save(
            MediaRecord(
                media_id=message.sender.remote_jid,
                message_id=media_record.message_id,
                file_name=renamed_file.file_name,
                relative_path=renamed_file.relative_path,
                mimetype=media_record.mimetype,
                size_bytes=renamed_file.size_bytes,
                sha256=renamed_file.sha256,
                absolute_path=renamed_file.absolute_path,
            )
        )
        return renamed_file
