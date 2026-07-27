from dataclasses import dataclass
from datetime import datetime, timezone

from app.core.config import settings
from app.services.category_service import CategoryService
from app.services.processing_queue import ProcessingJobStatus, ProcessingQueue
from app.services.storage_service import StorageService


@dataclass(frozen=True, slots=True)
class DashboardSnapshot:
    system_status: str
    evolution_status: str
    worker_status: str
    pending_jobs: int
    processing_jobs: int
    completed_jobs: int
    error_jobs: int


@dataclass(frozen=True, slots=True)
class AppSettingsSnapshot:
    downloads_root: str
    ffmpeg_path: str
    sqlite_database: str
    categories: list[str]


class DesktopDataProvider:
    def __init__(
        self,
        storage_service: StorageService,
        processing_queue: ProcessingQueue,
        category_service: CategoryService,
    ) -> None:
        self._storage_service = storage_service
        self._processing_queue = processing_queue
        self._category_service = category_service
        self._downloads_root = settings.FILE_STORAGE_ROOT
        self._ffmpeg_path = ""
        self._sqlite_database = settings.SQLITE_DATABASE_PATH

    def get_dashboard_snapshot(self) -> DashboardSnapshot:
        jobs = self._processing_queue.list_jobs()
        return DashboardSnapshot(
            system_status="Sistema Online",
            evolution_status="Desconhecida",
            worker_status="Ativo",
            pending_jobs=sum(1 for job in jobs if job.status is ProcessingJobStatus.PENDING),
            processing_jobs=sum(1 for job in jobs if job.status is ProcessingJobStatus.PROCESSING),
            completed_jobs=sum(1 for job in jobs if job.status is ProcessingJobStatus.COMPLETED),
            error_jobs=sum(1 for job in jobs if job.status is ProcessingJobStatus.ERROR),
        )

    def list_jobs(self) -> list[dict[str, str]]:
        return [
            {
                "id": job.id,
                "sender": job.sender,
                "origin": job.origin.value,
                "status": job.status.value,
                "created_at": job.created_at.isoformat(timespec="seconds"),
            }
            for job in self._processing_queue.list_jobs()
        ]

    def list_history(self, search_text: str = "") -> list[dict[str, str]]:
        normalized_search = search_text.strip().lower()
        rows = self._storage_service.list_media_history()
        filtered_rows: list[dict[str, str]] = []

        for row in rows:
            values = [str(value or "") for value in row.values()]
            if normalized_search and normalized_search not in " ".join(values).lower():
                continue

            filtered_rows.append(
                {
                    "date": str(row["date"]),
                    "sender": str(row["sender"]),
                    "category": str(row["category"] or ""),
                    "final_name": str(row["final_name"] or ""),
                    "file_path": str(row["file_path"] or ""),
                }
            )

        return filtered_rows

    def list_conversations(self) -> list[dict[str, str]]:
        sessions = self._storage_service.list_sessions()
        conversations: list[dict[str, str]] = []
        now = datetime.now(timezone.utc)

        for session in sessions:
            updated_at = float(session["updated_at"])
            wait_seconds = max(0, int(now.timestamp() - updated_at))
            conversations.append(
                {
                    "telefone": str(session["sender_id"]),
                    "sender": str(session["sender_id"]),
                    "status": "Ativa",
                    "categoria": str(session["category"] or "-"),
                    "arquivo recebido": "-",
                    "etapa atual": str(session["state"]),
                    "state": str(session["state"]),
                    "tempo de espera": f"{wait_seconds}s",
                }
            )

        return conversations

    def list_logs(self) -> list[dict[str, str]]:
        return [
            {
                "date": datetime.now(timezone.utc).isoformat(timespec="seconds"),
                "level": "INFO",
                "message": "Interface desktop atualizada.",
            }
        ]

    def get_settings_snapshot(self) -> AppSettingsSnapshot:
        return AppSettingsSnapshot(
            downloads_root=self._downloads_root,
            ffmpeg_path=self._ffmpeg_path,
            sqlite_database=self._sqlite_database,
            categories=self._category_service.list_categories(),
        )

    def update_settings(
        self,
        downloads_root: str,
        ffmpeg_path: str,
        sqlite_database: str,
        categories: list[str],
    ) -> None:
        self._downloads_root = downloads_root
        self._ffmpeg_path = ffmpeg_path
        self._sqlite_database = sqlite_database
        current_categories = self._category_service.list_categories()

        for category in current_categories:
            if category not in categories:
                self._category_service.remove(category)

        for category in categories:
            if category not in self._category_service.list_categories():
                self._category_service.add(category)

        self._category_service.reorder(categories)

    def clear_completed_jobs(self) -> int:
        return self._processing_queue.clear_completed()
