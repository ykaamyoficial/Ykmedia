from datetime import datetime
from pathlib import Path
from typing import Any

from app.core.config import settings
from app.models.files import FileLibraryItem, FileLibraryResponse
from app.services.storage_service import StorageService


class FileQueryService:
    def __init__(self, storage_service: StorageService) -> None:
        self._storage_service = storage_service

    def list_files(self) -> FileLibraryResponse:
        items = [self._build_item(row) for row in self._storage_service.list_media_history()]
        return FileLibraryResponse(items=items, total=len(items))

    def _build_item(self, row: dict[str, Any]) -> FileLibraryItem:
        final_name = str(row.get("final_name") or "")
        file_path = str(row.get("file_path") or "")
        absolute_path = self._resolve_media_path(file_path)
        return FileLibraryItem(
            id=str(row.get("id") or ""),
            date=str(row.get("date") or ""),
            date_display=self._format_datetime(str(row.get("date") or "")),
            sender=self._format_phone(str(row.get("sender") or "")),
            sender_raw=str(row.get("sender") or ""),
            origin=str(row.get("origin") or ""),
            category=str(row.get("category") or ""),
            final_name=final_name,
            file_path=file_path,
            absolute_path=str(absolute_path),
            kind=self._media_kind_from_name(final_name or file_path, str(row.get("origin") or "")),
            status=str(row.get("status") or ""),
            size=self._file_size(absolute_path),
            exists=absolute_path.exists(),
        )

    def _resolve_media_path(self, file_path: str) -> Path:
        path = Path(file_path)
        if path.is_absolute():
            return path
        return Path(settings.FILE_STORAGE_ROOT).resolve() / path

    def _format_phone(self, value: str) -> str:
        number = value.split("@", 1)[0]
        digits = "".join(character for character in number if character.isdigit())
        if len(digits) == 13 and digits.startswith("55"):
            return f"+55 {digits[2:4]} {digits[4:9]}-{digits[9:]}"
        if len(digits) == 12 and digits.startswith("55"):
            return f"+55 {digits[2:4]} {digits[4:8]}-{digits[8:]}"
        if digits:
            return f"+{digits}" if digits.startswith("55") else digits
        return value or "-"

    def _format_datetime(self, value: str) -> str:
        if not value:
            return "-"

        try:
            parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
        except ValueError:
            return value

        return parsed.strftime("%d/%m/%Y %H:%M")

    def _media_kind_from_name(self, file_name: str, origin: str = "") -> str:
        suffix = Path(file_name).suffix.lower()
        if origin.lower() == "youtube":
            return "YouTube"
        if suffix in {".jpg", ".jpeg", ".png", ".webp", ".gif"}:
            return "Imagem"
        if suffix in {".mp3", ".ogg", ".wav", ".m4a", ".aac", ".opus"}:
            return "Audio"
        if suffix in {".mp4", ".mov", ".mkv", ".webm", ".avi"}:
            return "Video"
        if suffix in {".pdf", ".doc", ".docx", ".xls", ".xlsx", ".ppt", ".pptx", ".txt"}:
            return "Documento"
        return "Arquivo"

    def _file_size(self, path: Path) -> str:
        if not path.exists():
            return "Tamanho indisponivel"
        size = path.stat().st_size
        if size >= 1024 * 1024:
            return f"{size / (1024 * 1024):.1f} MB"
        if size >= 1024:
            return f"{size / 1024:.1f} KB"
        return f"{size} B"
