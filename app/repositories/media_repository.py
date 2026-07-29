from threading import RLock
from typing import Protocol

from app.models.persistence import MediaRecord


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
