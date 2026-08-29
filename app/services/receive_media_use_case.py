import logging
import asyncio
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from pathlib import Path
import re
from typing import Any, Protocol
from uuid import uuid4

from app.core.config import settings
from app.models.download import DownloadedMedia
from app.models.interactive import InteractivePrompt
from app.models.persistence import (
    ConversationMessageDirection,
    ConversationMessageRecord,
    ConversationMessageStatus,
    MediaRecord,
)
from app.models.message import MessageType, ReceivedMessage
from app.models.storage import StoredFile
from app.repositories.conversation_message_repository import ConversationMessageRepository
from app.repositories.conversation_repository import ConversationRepository
from app.repositories.media_repository import MediaRepository
from app.services.conversation_engine import ConversationState
from app.services.conversation_engine import KEEP_ORIGINAL_FILENAME
from app.services.file_storage import FileStorage, FileStorageError
from app.services.message_catalog import WhatsAppMessageCatalog
from app.services.message_pipeline import MessagePipeline

logger = logging.getLogger(__name__)


class MediaHistoryRecorder(Protocol):
    def save_media_history(
        self,
        history_id: str,
        date: str,
        sender: str,
        origin: str,
        category: str | None,
        final_name: str | None,
        file_path: str | None,
        status: str,
    ) -> None:
        pass

    def save_contact_profile(
        self,
        sender: str,
        display_name: str | None = None,
        profile_picture_url: str | None = None,
        profile_picture_path: str | None = None,
        updated_at: str | None = None,
    ) -> None:
        pass


@dataclass(slots=True)
class _SenderSlot:
    """Serializa o processamento dos webhooks de um mesmo remetente."""

    lock: asyncio.Lock = field(default_factory=asyncio.Lock)
    waiters: int = 0


@dataclass(frozen=True, slots=True)
class ReceiveMediaResult:
    received_message: ReceivedMessage | None
    stored_file: StoredFile | None
    conversation_state: ConversationState | None
    next_message: str | None
    interactive_prompt: InteractivePrompt | None = None
    errors: list[str] = field(default_factory=list)


class ReceiveMediaUseCase:
    USAGE_INFO_INTERVAL = timedelta(days=1)

    def __init__(
        self,
        message_pipeline: MessagePipeline,
        media_repository: MediaRepository | None = None,
        conversation_repository: ConversationRepository | None = None,
        conversation_message_repository: ConversationMessageRepository | None = None,
        media_history_recorder: MediaHistoryRecorder | None = None,
        file_storage: FileStorage | None = None,
        media_grouping_window_seconds: float | None = None,
    ) -> None:
        self._message_pipeline = message_pipeline
        self._media_repository = media_repository
        self._conversation_repository = conversation_repository
        self._conversation_message_repository = conversation_message_repository
        self._media_history_recorder = media_history_recorder
        self._file_storage = file_storage
        self._media_grouping_window_seconds = (
            settings.MEDIA_GROUPING_WINDOW_SECONDS
            if media_grouping_window_seconds is None
            else max(0.0, media_grouping_window_seconds)
        )
        self._pending_downloads: dict[str, DownloadedMedia] = {}
        self._sender_slots: dict[str, _SenderSlot] = {}

    async def execute(self, payload: dict[str, Any]) -> ReceiveMediaResult:
        sender_id = self._extract_sender(payload)
        if not sender_id:
            return await self._execute(payload)

        slot = self._sender_slots.get(sender_id)
        if slot is None:
            slot = _SenderSlot()
            self._sender_slots[sender_id] = slot
        slot.waiters += 1
        await slot.lock.acquire()
        try:
            return await self._execute(payload, slot)
        finally:
            if slot.lock.locked():
                slot.lock.release()
            slot.waiters -= 1
            if slot.waiters <= 0:
                self._sender_slots.pop(sender_id, None)

    async def _execute(
        self,
        payload: dict[str, Any],
        slot: "_SenderSlot | None" = None,
    ) -> ReceiveMediaResult:
        previous_pending_media_ids = self._get_pending_media_ids_from_sender(
            self._extract_sender(payload)
        )
        pipeline_result = await self._message_pipeline.process_event(payload)
        conversation_result = pipeline_result.conversation_result
        command_result = pipeline_result.command_result
        received_message = pipeline_result.received_message
        stored_file = pipeline_result.stored_file
        errors = list(pipeline_result.errors)
        next_message_override: str | None = None

        if received_message is not None and pipeline_result.downloaded_media is not None:
            pending_media_id = pipeline_result.downloaded_media.message_id
            self._pending_downloads[pending_media_id] = pipeline_result.downloaded_media
            self._message_pipeline.conversation_engine.attach_pending_media(
                received_message.sender.remote_jid,
                pending_media_id,
            )

        if self._should_wait_for_media_grouping(
            received_message=received_message,
            conversation_result=conversation_result,
            downloaded_media=pipeline_result.downloaded_media,
        ):
            await self._wait_for_media_grouping(slot)
            refreshed_result = self._message_pipeline.conversation_engine.build_pending_category_response(
                received_message.sender.remote_jid,
                current_state=conversation_result.current_state,
            )
            if refreshed_result is not None:
                conversation_result = refreshed_result

        if self._is_silent_conversation_result(
            received_message=received_message,
            conversation_result=conversation_result,
            command_result=command_result,
            downloaded_media=pipeline_result.downloaded_media,
        ):
            if self._should_send_usage_info(received_message):
                self._record_inbound_message(
                    message=received_message,
                    state=conversation_result.next_state.value
                    if conversation_result is not None
                    else None,
                    media_id=None,
                    errors=errors,
                )
                return ReceiveMediaResult(
                    received_message=received_message,
                    stored_file=None,
                    conversation_state=conversation_result.next_state
                    if conversation_result is not None
                    else None,
                    next_message=WhatsAppMessageCatalog.usage_info(),
                    errors=errors,
                )
            return ReceiveMediaResult(
                received_message=received_message,
                stored_file=None,
                conversation_state=conversation_result.next_state
                if conversation_result is not None
                else None,
                next_message=None,
                errors=errors,
            )

        if (
            conversation_result is not None
            and conversation_result.is_finished
            and conversation_result.next_state is ConversationState.IDLE
            and conversation_result.suggested_response
            == WhatsAppMessageCatalog.conversation_timeout()
        ):
            self._discard_pending_media_ids(previous_pending_media_ids)

        if (
            received_message is not None
            and conversation_result is not None
            and conversation_result.next_state is ConversationState.FINISHED
            and conversation_result.current_state
            in {
                ConversationState.WAITING_CATEGORY_SELECTION,
                ConversationState.WAITING_FILENAME_DECISION,
                ConversationState.WAITING_CUSTOM_FILENAME,
            }
        ):
            try:
                renamed_file = self._store_pending_batch(received_message)
            except FileStorageError as exc:
                errors.append(f"storage: {exc}")
            else:
                if renamed_file is not None:
                    stored_file = renamed_file
                    self._message_pipeline.conversation_engine.reset(
                        received_message.sender.remote_jid
                    )
                else:
                    errors.append("storage: arquivo pendente nao encontrado para finalizar.")
                    next_message_override = WhatsAppMessageCatalog.pending_file_missing_finish()
                    self._message_pipeline.conversation_engine.reset(
                        received_message.sender.remote_jid
                    )

        self._record_inbound_message(
            message=received_message,
            state=conversation_result.next_state.value if conversation_result is not None else None,
            media_id=(
                pipeline_result.downloaded_media.message_id
                if pipeline_result.downloaded_media is not None
                else None
            ),
            errors=errors,
        )
        self._record_contact_profile(received_message)

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
            interactive_prompt=(
                conversation_result.interactive_prompt
                if conversation_result is not None
                else None
            ),
            errors=errors,
        )

    def _should_wait_for_media_grouping(
        self,
        received_message: ReceivedMessage | None,
        conversation_result: object,
        downloaded_media: DownloadedMedia | None,
    ) -> bool:
        return (
            self._media_grouping_window_seconds > 0
            and received_message is not None
            and downloaded_media is not None
            and conversation_result is not None
            and getattr(conversation_result, "current_state", None)
            is ConversationState.IDLE
            and getattr(conversation_result, "next_state", None)
            is ConversationState.WAITING_CATEGORY_SELECTION
            and bool(getattr(conversation_result, "suggested_response", ""))
        )

    async def _wait_for_media_grouping(self, slot: "_SenderSlot | None" = None) -> None:
        # Libera a serializacao do remetente durante a janela para que as demais
        # midias enviadas em sequencia sejam absorvidas neste mesmo lote.
        if slot is not None:
            slot.lock.release()
        try:
            await asyncio.sleep(self._media_grouping_window_seconds)
        finally:
            if slot is not None:
                await slot.lock.acquire()

    def _save_pending_media(
        self,
        media_id: str,
        stored_file: StoredFile,
        mimetype: str | None,
    ) -> None:
        if self._media_repository is None:
            return

        self._media_repository.save(
            MediaRecord(
                media_id=media_id,
                message_id=media_id,
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

        pending_media_id = self._get_pending_media_id(message)
        if pending_media_id is None:
            return None

        downloaded_media = self._pending_downloads.get(pending_media_id)
        if downloaded_media is None:
            return None

        stored_file = self._file_storage.save(downloaded_media)
        self._save_pending_media(
            media_id=downloaded_media.message_id,
            stored_file=stored_file,
            mimetype=downloaded_media.mimetype,
        )
        return stored_file

    def _store_pending_batch(self, message: ReceivedMessage) -> StoredFile | None:
        if self._file_storage is None:
            return None

        session = self._message_pipeline.conversation_engine.get_session(message.sender.remote_jid)
        if session is None or not session.category:
            return None

        pending_media_ids = session.pending_media_ids or (
            (session.pending_media_id,) if session.pending_media_id else ()
        )
        if not pending_media_ids:
            return None

        destination_folder = self._session_destination_folder(message, session.category)
        last_file: StoredFile | None = None

        for index, pending_media_id in enumerate(pending_media_ids, start=1):
            downloaded_media = self._pending_downloads.get(pending_media_id)
            if downloaded_media is None:
                continue

            stored_file = self._file_storage.save(downloaded_media)
            target_name = self._target_file_name(
                session_filename=session.filename,
                downloaded_media=downloaded_media,
                index=index,
                total=len(pending_media_ids),
            )
            moved_file = self._file_storage.move(
                stored_file=stored_file,
                destination_folder=destination_folder,
                new_file_name=target_name,
            )
            self._save_pending_media(
                media_id=downloaded_media.message_id,
                stored_file=moved_file,
                mimetype=downloaded_media.mimetype,
            )
            self._record_media_history(message, moved_file)
            self._pending_downloads.pop(pending_media_id, None)
            last_file = moved_file

        self._message_pipeline.conversation_engine.attach_pending_media(
            message.sender.remote_jid,
            None,
        )
        return last_file

    def _move_pending_media(self, message: ReceivedMessage) -> StoredFile | None:
        if self._media_repository is None or self._file_storage is None:
            return None

        pending_media_id = self._get_pending_media_id(message)
        if pending_media_id is None:
            return None

        media_record = self._media_repository.get_by_id(pending_media_id)
        if media_record is None or media_record.absolute_path is None:
            return None

        session = self._message_pipeline.conversation_engine.get_session(message.sender.remote_jid)
        if session is None or not session.filename or not session.category:
            return None

        target_name = (
            media_record.file_name
            if session.filename == KEEP_ORIGINAL_FILENAME
            else session.filename
        )

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
            new_file_name=target_name,
        )
        self._media_repository.save(
            MediaRecord(
                media_id=media_record.media_id,
                message_id=media_record.message_id,
                file_name=renamed_file.file_name,
                relative_path=renamed_file.relative_path,
                mimetype=media_record.mimetype,
                size_bytes=renamed_file.size_bytes,
                sha256=renamed_file.sha256,
                absolute_path=renamed_file.absolute_path,
            )
        )
        self._pending_downloads.pop(pending_media_id, None)
        self._message_pipeline.conversation_engine.attach_pending_media(
            message.sender.remote_jid,
            None,
        )
        return renamed_file

    def _get_pending_media_id(self, message: ReceivedMessage) -> str | None:
        return self._get_pending_media_id_from_sender(message.sender.remote_jid)

    def _get_pending_media_id_from_sender(self, sender_id: str | None) -> str | None:
        pending_media_ids = self._get_pending_media_ids_from_sender(sender_id)
        return pending_media_ids[-1] if pending_media_ids else None

    def _get_pending_media_ids_from_sender(self, sender_id: str | None) -> tuple[str, ...]:
        if not sender_id:
            return ()

        session = self._message_pipeline.conversation_engine.get_session(sender_id)
        if session is None:
            return ()

        if session.pending_media_ids:
            return session.pending_media_ids
        if session.pending_media_id:
            return (session.pending_media_id,)
        return ()

    def _extract_sender(self, payload: dict[str, Any]) -> str | None:
        data = payload.get("data")
        if not isinstance(data, dict):
            return None

        key = data.get("key")
        if not isinstance(key, dict):
            return None

        remote_jid = key.get("remoteJid")
        return str(remote_jid) if remote_jid else None

    def _discard_pending_media(self, message: ReceivedMessage) -> None:
        pending_media_id = self._get_pending_media_id(message)
        if pending_media_id is not None:
            self._pending_downloads.pop(pending_media_id, None)

    def _discard_pending_media_ids(self, media_ids: tuple[str, ...]) -> None:
        for media_id in media_ids:
            self._pending_downloads.pop(media_id, None)

    def _target_file_name(
        self,
        session_filename: str | None,
        downloaded_media: DownloadedMedia,
        index: int,
        total: int,
    ) -> str:
        if total > 1:
            return f"{index:03d}"
        if session_filename and session_filename != KEEP_ORIGINAL_FILENAME:
            return session_filename
        if downloaded_media.file_name:
            return Path(downloaded_media.file_name).stem
        return "001"

    def _record_inbound_message(
        self,
        message: ReceivedMessage | None,
        state: str | None,
        media_id: str | None,
        errors: list[str],
    ) -> None:
        if self._conversation_message_repository is None or message is None:
            return

        if "mensagem_duplicada" in errors:
            return

        logger.info(
            "Webhook media recebido: telefone=%s tipo=%s timestamp=%s media_id=%s",
            message.sender.remote_jid,
            message.message_type.value,
            datetime.now(timezone.utc).isoformat(timespec="microseconds"),
            media_id or "-",
        )

        self._conversation_message_repository.save(
            ConversationMessageRecord(
                id=str(uuid4()),
                message_id=message.message_id,
                sender=message.sender.remote_jid,
                direction=ConversationMessageDirection.INBOUND,
                content=self._message_content(message),
                message_type=message.message_type.value,
                state=state,
                media_id=media_id,
                created_at=datetime.now(timezone.utc).isoformat(timespec="microseconds"),
                status=(
                    ConversationMessageStatus.ERROR
                    if errors
                    else ConversationMessageStatus.RECEIVED
                ),
                error="; ".join(errors) if errors else None,
            )
        )

    def _record_media_history(self, message: ReceivedMessage, stored_file: StoredFile) -> None:
        if self._media_history_recorder is None:
            return

        session = self._message_pipeline.conversation_engine.get_session(message.sender.remote_jid)
        category = session.category if session is not None else None
        origin = "YouTube" if message.raw_type == "youtubeMessage" else "WhatsApp"
        self._media_history_recorder.save_media_history(
            history_id=str(uuid4()),
            date=datetime.now(timezone.utc).isoformat(timespec="microseconds"),
            sender=message.sender.remote_jid,
            origin=origin,
            category=category,
            final_name=stored_file.file_name,
            file_path=stored_file.relative_path,
            status="CONCLUIDO",
        )
        logger.info(
            "Midia persistida no historico: telefone=%s nome=%s caminho=%s hash=%s tipo=%s",
            message.sender.remote_jid,
            stored_file.file_name,
            stored_file.relative_path,
            stored_file.sha256,
            message.message_type.value,
        )

    def _session_destination_folder(self, message: ReceivedMessage, category: str) -> str:
        created_at = datetime.now(timezone.utc)
        session = self._message_pipeline.conversation_engine.get_session(message.sender.remote_jid)
        if session is not None and session.created_at is not None:
            created_at = datetime.fromtimestamp(session.created_at, tz=timezone.utc)
        contact_name = (
            message.sender.display_name
            or message.sender.remote_jid.split("@", 1)[0]
            or "contato"
        )
        safe_contact_name = re.sub(r"[^A-Za-z0-9_-]+", "_", contact_name).strip("_") or "contato"
        session_folder = f"{created_at.strftime('%Y-%m-%d_%H-%M')}_{safe_contact_name}"
        return str(Path(category) / session_folder)

    def _record_contact_profile(self, message: ReceivedMessage | None) -> None:
        if self._media_history_recorder is None or message is None:
            return
        if not message.sender.display_name and not message.sender.profile_picture_url:
            return
        self._media_history_recorder.save_contact_profile(
            sender=message.sender.remote_jid,
            display_name=message.sender.display_name,
            profile_picture_url=message.sender.profile_picture_url,
            updated_at=datetime.now(timezone.utc).isoformat(timespec="microseconds"),
        )

    def _message_content(self, message: ReceivedMessage) -> str:
        if message.text:
            return message.text

        if message.media is not None:
            if message.media.file_name:
                return f"Arquivo recebido: {message.media.file_name}"
            if message.media.caption:
                return f"Arquivo recebido: {message.media.caption}"

        return f"Mensagem recebida: {message.message_type.value}"

    def _is_silent_conversation_result(
        self,
        received_message: ReceivedMessage | None,
        conversation_result: object,
        command_result: object,
        downloaded_media: DownloadedMedia | None,
    ) -> bool:
        return (
            received_message is not None
            and command_result is None
            and downloaded_media is None
            and conversation_result is not None
            and getattr(conversation_result, "suggested_response", "") == ""
        )

    def _should_send_usage_info(self, message: ReceivedMessage | None) -> bool:
        if (
            message is None
            or message.message_type is not MessageType.TEXT
            or self._conversation_message_repository is None
        ):
            return False

        records = self._conversation_message_repository.list_by_sender(message.sender.remote_jid)
        if not records:
            return True

        latest_record = max(records, key=lambda record: record.created_at)
        try:
            latest_activity = datetime.fromisoformat(latest_record.created_at)
        except ValueError:
            return True
        if latest_activity.tzinfo is None:
            latest_activity = latest_activity.replace(tzinfo=timezone.utc)

        return datetime.now(timezone.utc) - latest_activity >= self.USAGE_INFO_INTERVAL
