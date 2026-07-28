from dataclasses import dataclass, field
from dataclasses import replace
from typing import Any, Callable, Protocol

from app.models.download import DownloadedMedia
from app.models.message import MessageType, ReceivedMessage
from app.models.storage import StoredFile
from app.services.command_processor import CommandProcessor, CommandResult
from app.services.conversation_engine import ConversationResult
from app.services.evolution_message_mapper import EvolutionMessageMappingResult, map_evolution_payload
from app.services.message_processor import ProcessingDecision, is_command_message, process_message
from app.services.processing_queue import (
    ProcessingJob,
    ProcessingJobOrigin,
    ProcessingQueue,
    ProcessingWorker,
)


class DownloadService(Protocol):
    async def download(self, message: ReceivedMessage) -> DownloadedMedia:
        pass


class StorageService(Protocol):
    def save(self, media: DownloadedMedia) -> StoredFile:
        pass


class ConversationService(Protocol):
    def handle(self, message: ReceivedMessage) -> ConversationResult:
        pass


class YoutubeDownloadService(Protocol):
    def extract_url(self, text: str | None) -> str | None:
        pass

    async def download(self, message: ReceivedMessage) -> DownloadedMedia:
        pass


@dataclass(frozen=True, slots=True)
class PipelineResult:
    received_message: ReceivedMessage | None
    processing_decision: ProcessingDecision | None
    downloaded_media: DownloadedMedia | None
    stored_file: StoredFile | None
    conversation_result: ConversationResult | None
    command_result: CommandResult | None = None
    errors: list[str] = field(default_factory=list)


class MessagePipeline:
    def __init__(
        self,
        download_manager: DownloadService,
        file_storage: StorageService,
        conversation_engine: ConversationService,
        command_processor: CommandProcessor | None = None,
        youtube_downloader: YoutubeDownloadService | None = None,
        processing_queue: ProcessingQueue | None = None,
        processing_worker: ProcessingWorker | None = None,
        payload_mapper: Callable[[dict[str, Any]], EvolutionMessageMappingResult] = map_evolution_payload,
        message_processor: Callable[[ReceivedMessage], ProcessingDecision] = process_message,
    ) -> None:
        self._download_manager = download_manager
        self._file_storage = file_storage
        self._conversation_engine = conversation_engine
        self._command_processor = command_processor
        self._youtube_downloader = youtube_downloader
        self._processing_queue = processing_queue or ProcessingQueue()
        self._processing_worker = processing_worker or ProcessingWorker()
        self._payload_mapper = payload_mapper
        self._message_processor = message_processor

    async def process_event(self, payload: dict[str, Any]) -> PipelineResult:
        job = self._processing_queue.enqueue(
            sender=self._extract_sender(payload),
            origin=self._detect_origin(payload),
            payload=payload,
        )
        result = await self._processing_worker.process_next(
            queue=self._processing_queue,
            handler=self._process_job,
        )
        if isinstance(result, PipelineResult):
            return result

        return PipelineResult(
            received_message=None,
            processing_decision=None,
            downloaded_media=None,
            stored_file=None,
            conversation_result=None,
            errors=[f"queue: trabalho {job.id} nao retornou resultado valido"],
        )

    async def _process_job(self, job: ProcessingJob) -> PipelineResult:
        return await self._process_payload(job.payload)

    async def _process_payload(self, payload: dict[str, Any]) -> PipelineResult:
        errors: list[str] = []
        mapping_result = self._payload_mapper(payload)

        if mapping_result.is_ignored or mapping_result.message is None:
            errors.append(mapping_result.ignored_reason or "mensagem_invalida")
            return PipelineResult(
                received_message=None,
                processing_decision=None,
                downloaded_media=None,
                stored_file=None,
                conversation_result=None,
                errors=errors,
            )

        message = mapping_result.message
        if is_command_message(message):
            command_result = self._process_command(message)
            return PipelineResult(
                received_message=message,
                processing_decision=None,
                downloaded_media=None,
                stored_file=None,
                conversation_result=None,
                command_result=command_result,
                errors=errors,
            )

        decision = self._message_processor(message)
        downloaded_media: DownloadedMedia | None = None
        stored_file: StoredFile | None = None
        downloaded_from_youtube = False

        if message.media is not None:
            try:
                downloaded_media = await self._download_manager.download(message)
            except Exception as exc:
                errors.append(self._format_error("download", exc))
        elif self._has_youtube_link(message):
            try:
                downloaded_media = await self._youtube_downloader.download(message)
                downloaded_from_youtube = True
            except Exception as exc:
                errors.append(self._format_error("youtube", exc))

        conversation_message = self._message_for_conversation(
            message=message,
            downloaded_from_youtube=downloaded_from_youtube,
        )
        conversation_result = self._conversation_engine.handle(conversation_message)

        return PipelineResult(
            received_message=message,
            processing_decision=decision,
            downloaded_media=downloaded_media,
            stored_file=stored_file,
            conversation_result=conversation_result,
            command_result=None,
            errors=errors,
        )

    def _format_error(self, stage: str, error: Exception) -> str:
        return f"{stage}: {error}"

    def _process_command(self, message: ReceivedMessage) -> CommandResult:
        if self._command_processor is not None:
            return self._command_processor.process(message)

        return CommandResult(
            command=message.text or "",
            response="Comandos indisponiveis nesta etapa.",
        )

    def _has_youtube_link(self, message: ReceivedMessage) -> bool:
        return (
            self._youtube_downloader is not None
            and self._youtube_downloader.extract_url(message.text) is not None
        )

    def _message_for_conversation(
        self,
        message: ReceivedMessage,
        downloaded_from_youtube: bool,
    ) -> ReceivedMessage:
        if not downloaded_from_youtube:
            return message

        return replace(
            message,
            message_type=MessageType.VIDEO,
            raw_type="youtubeMessage",
        )

    def _detect_origin(self, payload: dict[str, Any]) -> ProcessingJobOrigin:
        message = self._extract_message(payload)
        text = self._extract_text(message)
        if self._youtube_downloader is not None and self._youtube_downloader.extract_url(text) is not None:
            return ProcessingJobOrigin.YOUTUBE

        return ProcessingJobOrigin.WHATSAPP

    def _extract_sender(self, payload: dict[str, Any]) -> str:
        data = payload.get("data")
        if not isinstance(data, dict):
            return ""

        key = data.get("key")
        if not isinstance(key, dict):
            return ""

        return str(key.get("remoteJid") or "")

    def _extract_message(self, payload: dict[str, Any]) -> dict[str, Any]:
        data = payload.get("data")
        if not isinstance(data, dict):
            return {}

        message = data.get("message")
        return message if isinstance(message, dict) else {}

    def _extract_text(self, message: dict[str, Any]) -> str | None:
        conversation = message.get("conversation")
        if conversation is not None:
            return str(conversation)

        extended_text = message.get("extendedTextMessage")
        if isinstance(extended_text, dict):
            text = extended_text.get("text")
            return str(text) if text is not None else None

        return None

    @property
    def conversation_engine(self) -> ConversationService:
        return self._conversation_engine
