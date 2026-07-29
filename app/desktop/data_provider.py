from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Protocol

from app.core.config import settings
from app.desktop.formatters import (
    format_datetime,
    format_phone,
    initials_from_sender,
    media_kind_from_name,
)
from app.services.category_service import CategoryService
from app.services.backend_runtime_manager import BackendRuntimeSnapshot
from app.services.configuration_manager import AppConfigurationManager, SetupReport
from app.services.contact_profile_service import ContactProfileService
from app.services.diagnostic_service import DiagnosticReport
from app.services.environment_manager import EnvironmentCheck, EnvironmentManager
from app.services.processing_queue import ProcessingJobStatus, ProcessingQueue
from app.services.storage_service import StorageService
from app.services.system_startup_coordinator import StartupReport


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


class BackendRuntimeService(Protocol):
    def start(self) -> BackendRuntimeSnapshot:
        pass

    def stop(self) -> BackendRuntimeSnapshot:
        pass

    def restart(self) -> BackendRuntimeSnapshot:
        pass

    def snapshot(self) -> BackendRuntimeSnapshot:
        pass


class SystemStartupService(Protocol):
    def check(self) -> StartupReport:
        pass

    def prepare(self) -> StartupReport:
        pass


class DiagnosticRuntimeService(Protocol):
    def run(self) -> DiagnosticReport:
        pass

    def auto_fix(self) -> DiagnosticReport:
        pass

    def restart_backend(self) -> DiagnosticReport:
        pass


class AutomaticSetupRuntimeService(Protocol):
    def prepare(self) -> SetupReport:
        pass


class DesktopDataProvider:
    def __init__(
        self,
        storage_service: StorageService,
        processing_queue: ProcessingQueue,
        category_service: CategoryService,
        evolution_client: EvolutionSessionClient | None = None,
        environment_manager: EnvironmentManager | None = None,
        backend_runtime_manager: BackendRuntimeService | None = None,
        system_startup_coordinator: SystemStartupService | None = None,
        diagnostic_service: DiagnosticRuntimeService | None = None,
        automatic_setup_service: AutomaticSetupRuntimeService | None = None,
        configuration_manager: AppConfigurationManager | None = None,
        contact_profile_service: ContactProfileService | None = None,
    ) -> None:
        self._storage_service = storage_service
        self._processing_queue = processing_queue
        self._category_service = category_service
        self._evolution_client = evolution_client
        self._environment_manager = environment_manager
        self._backend_runtime_manager = backend_runtime_manager
        self._system_startup_coordinator = system_startup_coordinator
        self._diagnostic_service = diagnostic_service
        self._automatic_setup_service = automatic_setup_service
        self._configuration_manager = configuration_manager
        self._contact_profile_service = contact_profile_service
        self._downloads_root = settings.FILE_STORAGE_ROOT
        self._ffmpeg_path = settings.FFMPEG_PATH
        self._sqlite_database = settings.SQLITE_DATABASE_PATH

    def get_dashboard_snapshot(self) -> DashboardSnapshot:
        jobs = self._processing_queue.list_jobs()
        return DashboardSnapshot(
            system_status=self.get_backend_runtime_status(),
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
                "id": job.id[:8],
                "sender": format_phone(job.sender),
                "sender_raw": job.sender,
                "origin": job.origin.value,
                "status": job.status.value,
                "created_at": format_datetime(job.created_at.isoformat(timespec="seconds")),
                "file": self._extract_payload_file_label(job.payload),
                "kind": self._extract_payload_kind_label(job.payload),
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
                    "id": str(row["id"]),
                    "date": str(row["date"]),
                    "date_display": format_datetime(str(row["date"])),
                    "sender": format_phone(str(row["sender"])),
                    "sender_raw": str(row["sender"]),
                    "origin": str(row["origin"] or ""),
                    "category": str(row["category"] or ""),
                    "final_name": str(row["final_name"] or ""),
                    "file_path": str(row["file_path"] or ""),
                    "kind": media_kind_from_name(str(row["final_name"] or row["file_path"] or ""), str(row["origin"] or "")),
                    "status": str(row["status"] or ""),
                }
            )

        return filtered_rows

    def list_media_conversations(self, search_text: str = "") -> list[dict[str, object]]:
        contacts: list[dict[str, object]] = []
        for row in self._storage_service.list_media_contacts(search_text):
            sender_raw = str(row["sender"])
            contacts.append(
                {
                    "sender": format_phone(sender_raw),
                    "sender_raw": sender_raw,
                    "initials": initials_from_sender(sender_raw),
                    "display_name": self._display_name(sender_raw),
                    "profile_photo_path": self._contact_photo_path(sender_raw),
                    "last_activity": format_datetime(str(row["last_activity"])),
                    "last_media": str(row["last_media"] or "Arquivo"),
                    "media_count": int(row["media_count"] or 0),
                    "active": self._session_exists(sender_raw),
                    "items": self.list_media_files_by_sender(sender_raw),
                }
            )

        return contacts

    def ensure_contact_photo_cached(self, sender: str) -> str:
        if self._contact_profile_service is None:
            return ""
        return self._contact_profile_service.ensure_photo_cached(sender)

    def can_load_contact_photos(self) -> bool:
        return self._contact_profile_service is not None

    def list_media_files_by_sender(self, sender: str) -> list[dict[str, str]]:
        files: list[dict[str, str]] = []
        for row in self._storage_service.list_media_by_sender(sender):
            final_name = str(row["final_name"] or "")
            file_path = str(row["file_path"] or "")
            files.append(
                {
                    "id": str(row["id"]),
                    "date": str(row["date"]),
                    "date_display": format_datetime(str(row["date"])),
                    "sender": format_phone(str(row["sender"])),
                    "sender_raw": str(row["sender"]),
                    "origin": str(row["origin"] or ""),
                    "category": str(row["category"] or ""),
                    "final_name": final_name,
                    "file_path": file_path,
                    "kind": media_kind_from_name(final_name or file_path, str(row["origin"] or "")),
                    "status": str(row["status"] or ""),
                }
            )
        return files

    def list_conversation_threads(self, search_text: str = "") -> list[dict[str, object]]:
        normalized_search = search_text.strip().lower()
        contacts: dict[str, dict[str, object]] = {}
        history_by_sender: dict[str, list[dict[str, str]]] = {}
        for history in self.list_history():
            history_by_sender.setdefault(history["sender_raw"], []).append(history)

        for row in self._storage_service.list_conversation_contacts():
            sender_raw = str(row["sender"])
            formatted_sender = format_phone(sender_raw)
            last_content = str(row["last_content"] or "")
            history_rows = history_by_sender.get(sender_raw, [])
            session = self._storage_service.get_session(sender_raw)
            category = self._conversation_category(session, history_rows)
            generated_files = [
                str(history["final_name"] or history["file_path"])
                for history in history_rows
                if history.get("final_name") or history.get("file_path")
            ]
            status = str(row["last_status"] or "-")
            state = str(row["last_state"] or "-")
            search_blob = (
                f"{sender_raw} {formatted_sender} {last_content} {category} "
                f"{' '.join(generated_files)} {status} {state}"
            ).lower()
            if normalized_search and normalized_search not in search_blob:
                continue

            contacts[sender_raw] = {
                "sender": formatted_sender,
                "sender_raw": sender_raw,
                "initials": initials_from_sender(sender_raw),
                "display_name": self._display_name(sender_raw),
                "last_message": self._short_text(last_content, 44),
                "last_activity": format_datetime(str(row["last_activity"])),
                "last_activity_raw": str(row["last_activity"]),
                "message_count": int(row["message_count"] or 0),
                "active": session is not None,
                "state": state,
                "status": status,
                "category": category,
                "media_count": len(history_rows),
                "generated_files": generated_files,
                "folder": self._conversation_folder(category),
                "has_error": status == "ERRO" or any(history["status"] == "ERRO" for history in history_rows),
                "needs_response": session is not None and state not in {"FINISHED", "IDLE"},
                "download_pending": session is not None and not history_rows,
                "response_status": self._response_status(status),
                "download_status": self._download_status(history_rows),
                "first_message": self._first_conversation_message(sender_raw),
            }

        for session in self._storage_service.list_sessions():
            sender_raw = str(session["sender_id"])
            formatted_sender = format_phone(sender_raw)
            if normalized_search and normalized_search not in f"{sender_raw} {formatted_sender}".lower():
                continue
            contacts.setdefault(
                sender_raw,
                {
                    "sender": formatted_sender,
                    "sender_raw": sender_raw,
                    "initials": initials_from_sender(sender_raw),
                    "display_name": self._display_name(sender_raw),
                    "last_message": "Conversa ativa aguardando resposta.",
                    "last_activity": format_datetime(
                        datetime.fromtimestamp(
                            float(session["updated_at"]),
                            tz=timezone.utc,
                        ).isoformat(timespec="seconds")
                    ),
                    "last_activity_raw": str(session["updated_at"]),
                    "message_count": 0,
                    "active": True,
                    "state": str(session["state"]),
                    "status": "ATIVA",
                    "category": str(session["category"] or "-"),
                    "media_count": 0,
                    "generated_files": [],
                    "folder": self._conversation_folder(str(session["category"] or "-")),
                    "has_error": False,
                    "needs_response": str(session["state"]) not in {"FINISHED", "IDLE"},
                    "download_pending": True,
                    "response_status": "Pendente",
                    "download_status": "Pendente",
                    "first_message": "-",
                },
            )

        return sorted(
            contacts.values(),
            key=lambda item: str(item["last_activity_raw"]),
            reverse=True,
        )

    def list_conversation_timeline(self, sender: str) -> list[dict[str, str]]:
        rows = self._storage_service.list_conversation_messages(sender)
        timeline = [
            {
                "id": str(row["id"]),
                "message_id": str(row["message_id"]),
                "sender": format_phone(str(row["sender"])),
                "sender_raw": str(row["sender"]),
                "direction": str(row["direction"]),
                "content": str(row["content"]),
                "message_type": self._friendly_message_type(str(row["message_type"])),
                "state": str(row["state"] or "-"),
                "media_id": str(row["media_id"] or ""),
                "created_at": format_datetime(str(row["created_at"])),
                "created_at_raw": str(row["created_at"]),
                "status": str(row["status"] or ""),
                "error": str(row["error"] or ""),
            }
            for row in rows
        ]
        for history in self.list_history():
            if history["sender_raw"] != sender:
                continue
            timeline.append(
                {
                    "id": str(history["date"]),
                    "message_id": str(history["id"]),
                    "sender": format_phone(sender),
                    "sender_raw": sender,
                    "direction": "EVENT",
                    "content": f"Arquivo salvo: {history['final_name'] or history['file_path']}",
                    "message_type": history["kind"],
                    "state": history["category"] or "-",
                    "media_id": str(history["id"]),
                    "created_at": history["date_display"],
                    "created_at_raw": history["date"],
                    "status": history["status"],
                    "error": "",
                }
            )

        return sorted(timeline, key=lambda item: item["created_at_raw"])

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
                    "sender": format_phone(str(session["sender_id"])),
                    "sender_raw": str(session["sender_id"]),
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
        if self._configuration_manager is not None:
            self._configuration_manager.set_media_root(downloads_root)
            if ffmpeg_path:
                self._configuration_manager.set_ffmpeg_path(ffmpeg_path)
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
        session_id = sender_id
        for session in self._storage_service.list_sessions():
            raw_sender = str(session["sender_id"])
            if sender_id in {raw_sender, format_phone(raw_sender)}:
                session_id = raw_sender
                break

        self._storage_service.delete_session(session_id)

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

    def check_environment(self) -> EnvironmentCheck | None:
        if self._environment_manager is None:
            return None

        return self._environment_manager.check()

    def prepare_environment(self) -> EnvironmentCheck | None:
        if self._environment_manager is None:
            return None

        return self._environment_manager.prepare()

    def check_system_startup(self) -> StartupReport | None:
        if self._system_startup_coordinator is None:
            return None

        return self._system_startup_coordinator.check()

    def prepare_system_startup(self) -> StartupReport | None:
        if self._system_startup_coordinator is None:
            return None

        return self._system_startup_coordinator.prepare()

    def run_diagnostics(self) -> DiagnosticReport | None:
        if self._diagnostic_service is None:
            return None

        return self._diagnostic_service.run()

    def auto_fix_diagnostics(self) -> DiagnosticReport | None:
        if self._diagnostic_service is None:
            return None

        return self._diagnostic_service.auto_fix()

    def restart_backend_from_diagnostics(self) -> DiagnosticReport | None:
        if self._diagnostic_service is None:
            return None

        return self._diagnostic_service.restart_backend()

    def prepare_system_automatically(self) -> SetupReport | None:
        if self._automatic_setup_service is None:
            return None

        report = self._automatic_setup_service.prepare()
        self._downloads_root = settings.FILE_STORAGE_ROOT
        self._ffmpeg_path = settings.FFMPEG_PATH
        self._sqlite_database = settings.SQLITE_DATABASE_PATH
        return report

    def start_backend_runtime(self) -> BackendRuntimeSnapshot | None:
        if self._backend_runtime_manager is None:
            return None

        return self._backend_runtime_manager.start()

    def stop_backend_runtime(self) -> BackendRuntimeSnapshot | None:
        if self._backend_runtime_manager is None:
            return None

        return self._backend_runtime_manager.stop()

    def restart_backend_runtime(self) -> BackendRuntimeSnapshot | None:
        if self._backend_runtime_manager is None:
            return None

        return self._backend_runtime_manager.restart()

    def get_backend_runtime_status(self) -> str:
        if self._backend_runtime_manager is None:
            return "Sistema Online"

        return self._backend_runtime_manager.snapshot().state.value

    def media_root_path(self) -> Path:
        return Path(self._downloads_root).resolve()

    def resolve_media_file_path(self, file_path: str) -> Path:
        path = Path(file_path)
        if path.is_absolute():
            return path
        return self.media_root_path() / path

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

    def _extract_payload_file_label(self, payload: dict[str, object]) -> str:
        data = payload.get("data")
        if not isinstance(data, dict):
            return "-"
        message = data.get("message")
        if not isinstance(message, dict):
            return "-"
        for value in message.values():
            if isinstance(value, dict):
                file_name = value.get("fileName") or value.get("caption") or value.get("mimetype")
                if file_name:
                    return str(file_name)
            if isinstance(value, str) and "youtu" in value:
                return value
        return str(data.get("messageType") or "-")

    def _extract_payload_kind_label(self, payload: dict[str, object]) -> str:
        data = payload.get("data")
        if not isinstance(data, dict):
            return "Arquivo"
        raw_type = str(data.get("messageType") or "")
        labels = {
            "imageMessage": "Imagem",
            "audioMessage": "Audio",
            "videoMessage": "Video",
            "documentMessage": "Documento",
            "conversation": "Texto",
        }
        return labels.get(raw_type, "Arquivo")

    def _session_exists(self, sender_id: str) -> bool:
        return self._storage_service.get_session(sender_id) is not None

    def _conversation_category(
        self,
        session: dict[str, object] | None,
        history_rows: list[dict[str, str]],
    ) -> str:
        if session is not None and session.get("category"):
            return str(session["category"])
        for history in reversed(history_rows):
            if history.get("category"):
                return history["category"]
        return "-"

    def _conversation_folder(self, category: str) -> str:
        if not category or category == "-":
            return "-"
        return str(self.media_root_path() / category)

    def _download_status(self, history_rows: list[dict[str, str]]) -> str:
        if any(history["status"] == "ERRO" for history in history_rows):
            return "Erro"
        if history_rows:
            return "Concluido"
        return "Pendente"

    def _response_status(self, status: str) -> str:
        if status == "ENVIADA":
            return "Enviada"
        if status == "ERRO":
            return "Erro"
        return "Pendente"

    def _first_conversation_message(self, sender: str) -> str:
        messages = self._storage_service.list_conversation_messages(sender)
        if not messages:
            return "-"
        return self._short_text(str(messages[0]["content"]), 80)

    def _display_name(self, sender: str) -> str:
        profile = self._storage_service.get_contact_profile(sender)
        if profile:
            display_name = str(profile.get("display_name") or "").strip()
            if display_name:
                return display_name
        number = format_phone(sender)
        if number:
            return number
        return sender.split("@", 1)[0] or "Contato"

    def _contact_photo_path(self, sender: str) -> str:
        if self._contact_profile_service is not None:
            return self._contact_profile_service.get_cached_photo_path(sender)
        profile = self._storage_service.get_contact_profile(sender)
        return str(profile.get("profile_picture_path") or "") if profile else ""

    def _short_text(self, text: str, limit: int) -> str:
        normalized = " ".join(text.split())
        if len(normalized) <= limit:
            return normalized

        return f"{normalized[: limit - 3]}..."

    def _friendly_message_type(self, message_type: str) -> str:
        labels = {
            "texto": "Texto",
            "imagem": "Imagem",
            "audio": "Audio",
            "video": "Video",
            "documento": "Documento",
            "desconhecida": "Arquivo",
        }
        return labels.get(message_type.lower(), message_type)
