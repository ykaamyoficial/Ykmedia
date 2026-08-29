from threading import RLock
from typing import Protocol

from app.models.persistence import MediaRecord
from app.services.storage_service import StorageService


class MediaRepository(Protocol):
    def save(self, media: MediaRecord) -> None:
        pass

    def get_by_id(self, media_id: str) -> MediaRecord | None:
        pass

    def list(self) -> list[MediaRecord]:
        pass

    def exists(self, media_id: str) -> bool:
        pass

    def delete(self, media_id: str) -> None:
        pass


class InMemoryMediaRepository:
    def __init__(self) -> None:
        self._records: dict[str, MediaRecord] = {}
        self._lock = RLock()

    def save(self, media: MediaRecord) -> None:
        with self._lock:
            self._records[media.media_id] = media

    def get_by_id(self, media_id: str) -> MediaRecord | None:
        with self._lock:
            return self._records.get(media_id)

    def list(self) -> list[MediaRecord]:
        with self._lock:
            return list(self._records.values())

    def exists(self, media_id: str) -> bool:
        with self._lock:
            return media_id in self._records

    def delete(self, media_id: str) -> None:
        with self._lock:
            self._records.pop(media_id, None)


class SQLiteMediaRepository:
    def __init__(self, storage_service: StorageService) -> None:
        self._storage_service = storage_service

    def save(self, media: MediaRecord) -> None:
        self._storage_service.save_media_record(
            media_id=media.media_id,
            message_id=media.message_id,
            file_name=media.file_name,
            relative_path=media.relative_path,
            mimetype=media.mimetype,
            size_bytes=media.size_bytes,
            sha256=media.sha256,
            absolute_path=media.absolute_path,
        )

    def get_by_id(self, media_id: str) -> MediaRecord | None:
        row = self._storage_service.get_media_record(media_id)
        return self._row_to_record(row) if row is not None else None

    def list(self) -> list[MediaRecord]:
        return [self._row_to_record(row) for row in self._storage_service.list_media_records()]

    def exists(self, media_id: str) -> bool:
        return self._storage_service.get_media_record(media_id) is not None

    def delete(self, media_id: str) -> None:
        self._storage_service.delete_media_record(media_id)

    def _row_to_record(self, row: dict[str, object]) -> MediaRecord:
        return MediaRecord(
            media_id=str(row["media_id"]),
            message_id=str(row["message_id"]),
            file_name=str(row["file_name"]),
            relative_path=str(row["relative_path"]),
            mimetype=str(row["mimetype"]) if row.get("mimetype") is not None else None,
            size_bytes=int(row["size_bytes"]),  # type: ignore[arg-type]
            sha256=str(row["sha256"]),
            absolute_path=str(row["absolute_path"]) if row.get("absolute_path") is not None else None,
        )
