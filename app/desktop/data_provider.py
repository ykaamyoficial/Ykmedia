from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Protocol

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


@dataclass(frozen=True, slots=True)
class EvolutionSessionSnapshot:
    instance_name: str
    state: str
    qrcode_base64: str | None = None
    message: str | None = None


class EvolutionSessionClient(Protocol):
    async def connect_instance(self) -> dict[str, object]:
        pass

    async def get_connection_state(self) -> dict[str, object]:
        pass

    async def logout_instance(self) -> dict[str, object]:
        pass


class DesktopDataProvider:
    def __init__(
        self,
        storage_service: StorageService,
        processing_queue: ProcessingQueue,
        category_service: CategoryService,
        evolution_client: EvolutionSessionClient | None = None,
    ) -> None:
        self._storage_service = storage_service
        self._processing_queue = processing_queue
        self._category_service = category_service
        self._evolution_client = evolution_client
        self._downloads_root = settings.FILE_STORAGE_ROOT
        self._ffmpeg_path = settings.FFMPEG_PATH
        self._sqlite_database = settings.SQLITE_DATABASE_PATH

    def get_dashboard_snapshot(self) -> DashboardSnapshot:
        jobs = self._processing_queue.list_jobs()
        return DashboardSnapshot(
            system_status="Sistema Online",
            evolution_status=self.get_evolution_session_snapshot().state,
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

    def list_logs(self, search_text: str = "", level: str = "Todos") -> list[dict[str, str]]:
        normalized_search = search_text.strip().lower()
        selected_level = level.strip().upper()
        rows: list[dict[str, str]] = []

        for line in self._read_log_lines():
            detected_level = self._detect_log_level(line)
            if selected_level != "TODOS" and detected_level != selected_level:
                continue
            if normalized_search and normalized_search not in line.lower():
                continue

            rows.append(
                {
                    "date": datetime.now(timezone.utc).isoformat(timespec="seconds"),
                    "level": detected_level,
                    "message": line,
                }
            )

        if rows:
            return rows

        return [
            {
                "date": datetime.now(timezone.utc).isoformat(timespec="seconds"),
                "level": "INFO",
                "message": "Nenhum log encontrado.",
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
        settings.FILE_STORAGE_ROOT = downloads_root
        settings.FFMPEG_PATH = ffmpeg_path
        settings.SQLITE_DATABASE_PATH = sqlite_database
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

    def delete_conversation(self, sender_id: str) -> None:
        self._storage_service.delete_session(sender_id)

    def get_evolution_session_snapshot(self) -> EvolutionSessionSnapshot:
        if self._evolution_client is None:
            return EvolutionSessionSnapshot(
                instance_name=settings.EVOLUTION_INSTANCE,
                state="Desconhecida",
                message="Cliente Evolution indisponivel na interface.",
            )

        try:
            payload = self._run_async(self._evolution_client.get_connection_state())
        except Exception as exc:
            return EvolutionSessionSnapshot(
                instance_name=settings.EVOLUTION_INSTANCE,
                state="Erro",
                message=str(exc),
            )

        return EvolutionSessionSnapshot(
            instance_name=settings.EVOLUTION_INSTANCE,
            state=self._extract_connection_state(payload),
            message="Estado atualizado.",
        )

    def connect_evolution_session(self) -> EvolutionSessionSnapshot:
        if self._evolution_client is None:
            return EvolutionSessionSnapshot(
                instance_name=settings.EVOLUTION_INSTANCE,
                state="Erro",
                message="Cliente Evolution indisponivel na interface.",
            )

        try:
            payload = self._run_async(self._evolution_client.connect_instance())
        except Exception as exc:
            return EvolutionSessionSnapshot(
                instance_name=settings.EVOLUTION_INSTANCE,
                state="Erro",
                message=str(exc),
            )

        return EvolutionSessionSnapshot(
            instance_name=settings.EVOLUTION_INSTANCE,
            state=self._extract_connection_state(payload),
            qrcode_base64=self._extract_qrcode_base64(payload),
            message="QR Code solicitado.",
        )

    def disconnect_evolution_session(self) -> EvolutionSessionSnapshot:
        if self._evolution_client is None:
            return EvolutionSessionSnapshot(
                instance_name=settings.EVOLUTION_INSTANCE,
                state="Erro",
                message="Cliente Evolution indisponivel na interface.",
            )

        try:
            payload = self._run_async(self._evolution_client.logout_instance())
        except Exception as exc:
            return EvolutionSessionSnapshot(
                instance_name=settings.EVOLUTION_INSTANCE,
                state="Erro",
                message=str(exc),
            )

        return EvolutionSessionSnapshot(
            instance_name=settings.EVOLUTION_INSTANCE,
            state=self._extract_connection_state(payload) or "close",
            message="Sessao desconectada.",
        )

    def reconnect_evolution_session(self) -> EvolutionSessionSnapshot:
        disconnected = self.disconnect_evolution_session()
        if disconnected.state == "Erro":
            return disconnected

        return self.connect_evolution_session()

    def media_root_path(self) -> Path:
        return Path(self._downloads_root).resolve()

    def sqlite_database_path(self) -> Path:
        return Path(self._sqlite_database).resolve()

    def logs_directory_path(self) -> Path:
        return Path("logs").resolve()

    def export_logs(self, target_path: str | Path) -> int:
        rows = self.list_logs()
        content = "\n".join(
            f"{row['date']} [{row['level']}] {row['message']}"
            for row in rows
        )
        path = Path(target_path).resolve()
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")
        return len(rows)

    def _read_log_lines(self) -> list[str]:
        logs_directory = self.logs_directory_path()
        if not logs_directory.exists():
            return []

        lines: list[str] = []
        for log_file in sorted(logs_directory.glob("*.log"), key=lambda path: path.stat().st_mtime):
            try:
                file_lines = log_file.read_text(encoding="utf-8", errors="replace").splitlines()
            except OSError:
                continue
            lines.extend(line.strip() for line in file_lines if line.strip())

        return lines[-300:]

    def _detect_log_level(self, line: str) -> str:
        upper_line = line.upper()
        if "ERROR" in upper_line or "ERRO" in upper_line:
            return "ERROR"
        if "WARNING" in upper_line or "WARN" in upper_line:
            return "WARNING"
        return "INFO"

    def _run_async(self, awaitable):
        import asyncio

        return asyncio.run(awaitable)

    def _extract_connection_state(self, payload: dict[str, object]) -> str:
        instance = payload.get("instance")
        if isinstance(instance, dict):
            state = instance.get("state") or instance.get("status") or instance.get("connectionStatus")
            if state is not None:
                return str(state)

        state = payload.get("state") or payload.get("status") or payload.get("connectionStatus")
        return str(state) if state is not None else "Desconhecida"

    def _extract_qrcode_base64(self, payload: dict[str, object]) -> str | None:
        qrcode = payload.get("qrcode")
        if isinstance(qrcode, dict):
            base64_value = qrcode.get("base64")
            return str(base64_value) if base64_value else None

        base64_value = payload.get("base64")
        return str(base64_value) if base64_value else None
