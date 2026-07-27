from functools import lru_cache

from app.core.config import settings
from app.repositories.conversation_repository import InMemoryConversationRepository
from app.repositories.media_repository import InMemoryMediaRepository
from app.services.category_service import CategoryService
from app.services.command_processor import CommandProcessor
from app.services.conversation_engine import ConversationEngine
from app.services.download_manager import DownloadManager
from app.services.evolution_client import EvolutionClient
from app.services.file_storage import FileStorage
from app.services.message_pipeline import MessagePipeline
from app.services.processing_queue import ProcessingQueue, ProcessingWorker
from app.services.receive_media_use_case import ReceiveMediaUseCase
from app.services.session_store import SQLiteSessionStore
from app.services.storage_service import StorageService
from app.services.youtube_downloader import YoutubeDownloader


@lru_cache(maxsize=1)
def get_evolution_client() -> EvolutionClient:
    return EvolutionClient()


@lru_cache(maxsize=1)
def get_storage_service() -> StorageService:
    return StorageService(database_path=settings.SQLITE_DATABASE_PATH)


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
def get_media_repository() -> InMemoryMediaRepository:
    return InMemoryMediaRepository()


@lru_cache(maxsize=1)
def get_conversation_repository() -> InMemoryConversationRepository:
    return InMemoryConversationRepository()


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
    )
    return ReceiveMediaUseCase(
        message_pipeline=message_pipeline,
        media_repository=get_media_repository(),
        conversation_repository=get_conversation_repository(),
        file_storage=file_storage,
    )
