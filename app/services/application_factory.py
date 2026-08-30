from functools import lru_cache
import time

from app.core.config import settings
from app.repositories.conversation_message_repository import SQLiteConversationMessageRepository
from app.repositories.media_repository import SQLiteMediaRepository
from app.repositories.pending_media_repository import SQLitePendingMediaRepository
from app.repositories.processed_message_repository import SQLiteProcessedMessageRepository
from app.services.configuration_manager import (
    AppConfigurationManager,
    AutomaticSetupService,
    EvolutionProvisioningManager,
    FfmpegManager,
)
from app.services.contact_profile_service import ContactProfileService
from app.services.category_service import CategoryService
from app.services.category_query_service import CategoryQueryService
from app.services.backend_runtime_manager import BackendRuntimeManager
from app.services.command_processor import CommandProcessor
from app.services.conversation_engine import ConversationEngine
from app.services.conversation_query_service import ConversationQueryService
from app.services.dashboard_service import DashboardService
from app.services.download_manager import DownloadManager
from app.services.diagnostic_service import DiagnosticService
from app.services.download_query_service import DownloadQueryService
from app.services.evolution_client import EvolutionClient
from app.services.evolution_license_service import EvolutionLicenseService
from app.services.environment_manager import EnvironmentManager
from app.services.file_query_service import FileQueryService
from app.services.file_storage import FileStorage
from app.services.history_query_service import HistoryQueryService
from app.services.message_pipeline import MessagePipeline
from app.services.message_response_sender import MessageResponseSender
from app.services.processing_queue import ProcessingQueue, ProcessingWorker
from app.services.queue_retry_worker import QueueRetryWorker, WebhookJobReprocessor
from app.services.session_expiry_notifier import SessionExpiryNotifier
from app.services.receive_media_use_case import ReceiveMediaUseCase
from app.services.session_store import SQLiteSessionStore
from app.services.settings_query_service import SettingsQueryService
from app.services.storage_service import StorageService
from app.services.system_startup_coordinator import SystemStartupCoordinator
from app.services.youtube_downloader import YoutubeDownloader


@lru_cache(maxsize=1)
def get_evolution_client() -> EvolutionClient:
    return EvolutionClient()


@lru_cache(maxsize=1)
def get_evolution_license_service() -> EvolutionLicenseService:
    return EvolutionLicenseService()


@lru_cache(maxsize=1)
def get_storage_service() -> StorageService:
    return StorageService(database_path=settings.SQLITE_DATABASE_PATH)


@lru_cache(maxsize=1)
def get_dashboard_service() -> DashboardService:
    return DashboardService(
        storage_service=get_storage_service(),
        evolution_client=get_evolution_client(),
    )


@lru_cache(maxsize=1)
def get_conversation_query_service() -> ConversationQueryService:
    return ConversationQueryService(storage_service=get_storage_service())


@lru_cache(maxsize=1)
def get_session_store() -> SQLiteSessionStore:
    return SQLiteSessionStore(
        storage_service=get_storage_service(),
        ttl_seconds=settings.CONVERSATION_SESSION_TTL_SECONDS,
    )


@lru_cache(maxsize=1)
def get_category_service() -> CategoryService:
    return CategoryService(storage_service=get_storage_service())


@lru_cache(maxsize=1)
def get_category_query_service() -> CategoryQueryService:
    return CategoryQueryService(category_service=get_category_service())


@lru_cache(maxsize=1)
def get_conversation_engine() -> ConversationEngine:
    return ConversationEngine(
        session_store=get_session_store(),
        category_service=get_category_service(),
    )


@lru_cache(maxsize=1)
def get_command_processor() -> CommandProcessor:
    return CommandProcessor(conversation_engine=get_conversation_engine())


@lru_cache(maxsize=1)
def get_youtube_downloader() -> YoutubeDownloader:
    return YoutubeDownloader()


@lru_cache(maxsize=1)
def get_processing_queue() -> ProcessingQueue:
    return ProcessingQueue(storage_service=get_storage_service())


@lru_cache(maxsize=1)
def get_processing_worker() -> ProcessingWorker:
    return ProcessingWorker()


@lru_cache(maxsize=1)
def get_session_expiry_notifier() -> SessionExpiryNotifier:
    return SessionExpiryNotifier(
        storage_service=get_storage_service(),
        evolution_client=get_evolution_client(),
        warning_seconds=settings.SESSION_EXPIRY_WARNING_SECONDS,
    )


@lru_cache(maxsize=1)
def get_queue_retry_worker() -> QueueRetryWorker:
    return QueueRetryWorker(
        queue=get_processing_queue(),
        reprocessor=WebhookJobReprocessor(
            use_case=get_receive_media_use_case(),
            response_sender=get_message_response_sender(),
        ),
    )


@lru_cache(maxsize=1)
def get_download_query_service() -> DownloadQueryService:
    return DownloadQueryService(processing_queue=get_processing_queue())


@lru_cache(maxsize=1)
def get_file_query_service() -> FileQueryService:
    return FileQueryService(storage_service=get_storage_service())


@lru_cache(maxsize=1)
def get_history_query_service() -> HistoryQueryService:
    return HistoryQueryService(storage_service=get_storage_service())


@lru_cache(maxsize=1)
def get_media_repository() -> SQLiteMediaRepository:
    return SQLiteMediaRepository(storage_service=get_storage_service())


@lru_cache(maxsize=1)
def get_pending_media_repository() -> SQLitePendingMediaRepository:
    repository = SQLitePendingMediaRepository(
        storage_service=get_storage_service(),
        staging_root=settings.FILE_STORAGE_ROOT,
    )
    # Descarta bytes orfaos de conversas que ja expiraram sem serem concluidas.
    repository.purge_older_than(time.time() - settings.CONVERSATION_SESSION_TTL_SECONDS)
    return repository


@lru_cache(maxsize=1)
def get_conversation_message_repository() -> SQLiteConversationMessageRepository:
    return SQLiteConversationMessageRepository(storage_service=get_storage_service())


@lru_cache(maxsize=1)
def get_processed_message_repository() -> SQLiteProcessedMessageRepository:
    return SQLiteProcessedMessageRepository(storage_service=get_storage_service())


@lru_cache(maxsize=1)
def get_message_response_sender() -> MessageResponseSender:
    return MessageResponseSender(
        evolution_client=get_evolution_client(),
        conversation_message_repository=get_conversation_message_repository(),
    )


@lru_cache(maxsize=1)
def get_environment_manager() -> EnvironmentManager:
    return EnvironmentManager()


@lru_cache(maxsize=1)
def get_backend_runtime_manager() -> BackendRuntimeManager:
    return BackendRuntimeManager()


@lru_cache(maxsize=1)
def get_system_startup_coordinator() -> SystemStartupCoordinator:
    return SystemStartupCoordinator(
        environment_manager=get_environment_manager(),
        backend_runtime_manager=get_backend_runtime_manager(),
        evolution_client=get_evolution_client(),
    )


@lru_cache(maxsize=1)
def get_diagnostic_service() -> DiagnosticService:
    return DiagnosticService(
        environment_manager=get_environment_manager(),
        backend_runtime_manager=get_backend_runtime_manager(),
        startup_coordinator=get_system_startup_coordinator(),
        evolution_client=get_evolution_client(),
    )


@lru_cache(maxsize=1)
def get_contact_profile_service() -> ContactProfileService:
    return ContactProfileService(
        storage_service=get_storage_service(),
        evolution_client=get_evolution_client(),
    )


@lru_cache(maxsize=1)
def get_configuration_manager() -> AppConfigurationManager:
    return AppConfigurationManager()


@lru_cache(maxsize=1)
def get_ffmpeg_manager() -> FfmpegManager:
    return FfmpegManager(configuration_manager=get_configuration_manager())


@lru_cache(maxsize=1)
def get_evolution_provisioning_manager() -> EvolutionProvisioningManager:
    return EvolutionProvisioningManager(evolution_client=get_evolution_client())


@lru_cache(maxsize=1)
def get_automatic_setup_service() -> AutomaticSetupService:
    return AutomaticSetupService(
        configuration_manager=get_configuration_manager(),
        environment_manager=get_environment_manager(),
        backend_runtime_manager=get_backend_runtime_manager(),
        evolution_provisioning_manager=get_evolution_provisioning_manager(),
        diagnostic_service=get_diagnostic_service(),
        ffmpeg_manager=get_ffmpeg_manager(),
        license_service=get_evolution_license_service(),
    )


@lru_cache(maxsize=1)
def get_settings_query_service() -> SettingsQueryService:
    return SettingsQueryService(
        configuration_manager=get_configuration_manager(),
        diagnostic_service=get_diagnostic_service(),
        automatic_setup_service=get_automatic_setup_service(),
        evolution_provisioning_manager=get_evolution_provisioning_manager(),
        evolution_client=get_evolution_client(),
    )


@lru_cache(maxsize=1)
def get_receive_media_use_case() -> ReceiveMediaUseCase:
    evolution_client = get_evolution_client()
    download_manager = DownloadManager(evolution_client)
    file_storage = FileStorage()
    conversation_engine = get_conversation_engine()
    message_pipeline = MessagePipeline(
        download_manager=download_manager,
        file_storage=file_storage,
        conversation_engine=conversation_engine,
        command_processor=get_command_processor(),
        youtube_downloader=get_youtube_downloader(),
        processing_queue=get_processing_queue(),
        processing_worker=get_processing_worker(),
        processed_message_repository=get_processed_message_repository(),
    )
    return ReceiveMediaUseCase(
        message_pipeline=message_pipeline,
        media_repository=get_media_repository(),
        pending_media_repository=get_pending_media_repository(),
        conversation_message_repository=get_conversation_message_repository(),
        media_history_recorder=get_storage_service(),
        file_storage=file_storage,
    )
