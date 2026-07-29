import sqlite3
import time
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Protocol

from app.core.config import settings
from app.models.dashboard import (
    DashboardConversationMessage,
    DashboardConversationsInfo,
    DashboardDownloadsInfo,
    DashboardEvolutionInfo,
    DashboardFilesInfo,
    DashboardHealthItem,
    DashboardHistoryItem,
    DashboardOverview,
    DashboardSystemInfo,
    DashboardWhatsAppInfo,
)
from app.services.processing_queue import ProcessingJobStatus
from app.services.storage_service import StorageService

_STARTED_AT = time.monotonic()


class EvolutionDashboardClient(Protocol):
    async def health(self) -> dict[str, Any]:
        pass

    async def get_connection_state(self) -> dict[str, Any]:
        pass


class DashboardService:
    def __init__(
        self,
        storage_service: StorageService,
        evolution_client: EvolutionDashboardClient,
        media_root: str | Path | None = None,
    ) -> None:
        self._storage_service = storage_service
        self._evolution_client = evolution_client
        self._media_root = Path(media_root or settings.FILE_STORAGE_ROOT)

    async def get_overview(self) -> DashboardOverview:
        jobs = self._storage_service.list_processing_jobs()
        history = self._storage_service.list_media_history()
        sessions = self._storage_service.list_sessions()
        categories = self._storage_service.list_categories()
        conversation_contacts = self._storage_service.list_conversation_contacts()
        database_connected = self._database_connected()
        evolution, whatsapp = await self._build_external_status()
        downloads = self._build_downloads(jobs)
        files = self._build_files(history, categories)
        conversations = self._build_conversations(sessions, conversation_contacts)

        return DashboardOverview(
            generated_at=datetime.now(timezone.utc).isoformat(timespec="seconds"),
            system=DashboardSystemInfo(
                version=settings.APP_VERSION,
                uptime_seconds=int(time.monotonic() - _STARTED_AT),
                backend_online=True,
                database_connected=database_connected,
            ),
            evolution=evolution,
            whatsapp=whatsapp,
            downloads=downloads,
            files=files,
            conversations=conversations,
            history=self._build_history(history),
            health=self._build_health(database_connected, evolution, whatsapp),
            has_data=bool(history or jobs or sessions or categories or conversation_contacts),
        )

    def _build_downloads(self, jobs: list[dict[str, Any]]) -> DashboardDownloadsInfo:
        counts = Counter(str(job["status"]) for job in jobs)
        return DashboardDownloadsInfo(
            in_progress=counts[ProcessingJobStatus.PROCESSING.value],
            completed=counts[ProcessingJobStatus.COMPLETED.value],
            failures=counts[ProcessingJobStatus.ERROR.value],
            queue=counts[ProcessingJobStatus.PENDING.value],
        )

    def _build_files(
        self,
        history: list[dict[str, Any]],
        categories: list[str],
    ) -> DashboardFilesInfo:
        return DashboardFilesInfo(
            stored_count=len(history),
            storage_used_bytes=self._storage_used_bytes(history),
            categories=categories,
        )

    def _build_conversations(
        self,
        sessions: list[dict[str, Any]],
        contacts: list[dict[str, Any]],
    ) -> DashboardConversationsInfo:
        return DashboardConversationsInfo(
            total=len(contacts),
            active_contacts=len(sessions),
            latest_messages=[
                DashboardConversationMessage(
                    sender=str(contact["sender"]),
                    last_content=(
                        str(contact["last_content"])
                        if contact.get("last_content") is not None
                        else None
                    ),
                    last_activity=(
                        str(contact["last_activity"])
                        if contact.get("last_activity") is not None
                        else None
                    ),
                    status=str(contact["last_status"]),
                    message_count=int(contact["message_count"]),
                )
                for contact in contacts[:5]
            ],
        )

    def _build_history(self, history: list[dict[str, Any]]) -> list[DashboardHistoryItem]:
        rows = sorted(
            history,
            key=lambda record: (str(record["date"]), str(record["id"])),
            reverse=True,
        )
        return [
            DashboardHistoryItem(
                id=str(record["id"]),
                date=str(record["date"]),
                sender=str(record["sender"]),
                origin=str(record["origin"]),
                category=(
                    str(record["category"]) if record.get("category") is not None else None
                ),
                final_name=(
                    str(record["final_name"])
                    if record.get("final_name") is not None
                    else None
                ),
                file_path=(
                    str(record["file_path"]) if record.get("file_path") is not None else None
                ),
                status=str(record["status"]),
            )
            for record in rows[:5]
        ]

    async def _build_external_status(
        self,
    ) -> tuple[DashboardEvolutionInfo, DashboardWhatsAppInfo]:
        sync_time = datetime.now(timezone.utc).isoformat(timespec="seconds")
        try:
            await self._evolution_client.health()
            connection_payload = await self._evolution_client.get_connection_state()
        except Exception as exc:
            return (
                DashboardEvolutionInfo(
                    online=False,
                    instance=settings.EVOLUTION_INSTANCE,
                    error=exc.__class__.__name__,
                ),
                DashboardWhatsAppInfo(
                    status="offline",
                    connected=False,
                    qr_pending=True,
                ),
            )

        state = self._extract_connection_state(connection_payload)
        connected = state == "open"
        qr_pending = state in {"close", "closed", "connecting", "unknown", ""}
        return (
            DashboardEvolutionInfo(
                online=True,
                instance=settings.EVOLUTION_INSTANCE,
                last_sync=sync_time,
            ),
            DashboardWhatsAppInfo(
                status="connected" if connected else "qr_pending" if qr_pending else state,
                connected=connected,
                qr_pending=qr_pending and not connected,
            ),
        )

    def _build_health(
        self,
        database_connected: bool,
        evolution: DashboardEvolutionInfo,
        whatsapp: DashboardWhatsAppInfo,
    ) -> list[DashboardHealthItem]:
        storage_ready = self._media_root.exists() and self._media_root.is_dir()
        return [
            DashboardHealthItem(
                key="backend",
                label="Backend",
                status="online",
                description="API FastAPI respondendo.",
            ),
            DashboardHealthItem(
                key="database",
                label="Banco",
                status="online" if database_connected else "offline",
                description="SQLite conectado."
                if database_connected
                else "SQLite indisponivel.",
            ),
            DashboardHealthItem(
                key="evolution",
                label="Evolution",
                status="online" if evolution.online else "offline",
                description="Evolution acessivel."
                if evolution.online
                else "Evolution indisponivel.",
            ),
            DashboardHealthItem(
                key="whatsapp",
                label="WhatsApp",
                status="online" if whatsapp.connected else "warning",
                description="WhatsApp conectado."
                if whatsapp.connected
                else "WhatsApp aguardando conexao.",
            ),
            DashboardHealthItem(
                key="storage",
                label="Storage",
                status="online" if storage_ready else "warning",
                description="Pasta de midias encontrada."
                if storage_ready
                else "Pasta de midias ainda nao criada.",
            ),
        ]

    def _storage_used_bytes(self, history: list[dict[str, Any]]) -> int:
        total = 0
        for record in history:
            file_path = record.get("file_path")
            if file_path is None:
                continue
            path = Path(str(file_path))
            if not path.is_absolute():
                path = self._media_root / path
            try:
                if path.is_file():
                    total += path.stat().st_size
            except OSError:
                continue
        return total

    def _database_connected(self) -> bool:
        try:
            with sqlite3.connect(self._storage_service.database_path) as connection:
                connection.execute("SELECT 1")
        except (OSError, sqlite3.Error):
            return False
        return True

    def _extract_connection_state(self, payload: dict[str, Any]) -> str:
        instance = payload.get("instance")
        if isinstance(instance, dict):
            value = instance.get("state") or instance.get("status") or instance.get("connectionStatus")
            if value is not None:
                return str(value).lower()

        value = payload.get("state") or payload.get("status") or payload.get("connectionStatus")
        return str(value).lower() if value is not None else "unknown"
