"""Armazena as midias ja baixadas da Evolution que aguardam o usuario concluir
o fluxo da conversa (escolher categoria e nome).

Antes esses bytes viviam num `dict` em memoria: se o backend reiniciava no meio
de uma conversa, o arquivo era perdido. Agora os bytes vao para um arquivo de
staging e os metadados para o SQLite, sobrevivendo a reinicios.
"""

import hashlib
import time
from pathlib import Path
from threading import RLock
from typing import Protocol

from app.models.download import DownloadedMedia
from app.services.storage_service import StorageService


class PendingMediaRepository(Protocol):
    def save(self, media: DownloadedMedia, sender: str) -> None: ...

    def get(self, message_id: str) -> DownloadedMedia | None: ...

    def delete(self, message_id: str) -> None: ...

    def purge_older_than(self, cutoff_epoch: float) -> int: ...


class InMemoryPendingMediaRepository:
    def __init__(self) -> None:
        self._items: dict[str, DownloadedMedia] = {}
        self._lock = RLock()

    def save(self, media: DownloadedMedia, sender: str) -> None:
        with self._lock:
            self._items[media.message_id] = media

    def get(self, message_id: str) -> DownloadedMedia | None:
        with self._lock:
            return self._items.get(message_id)

    def delete(self, message_id: str) -> None:
        with self._lock:
            self._items.pop(message_id, None)

    def purge_older_than(self, cutoff_epoch: float) -> int:
        return 0


class SQLitePendingMediaRepository:
    def __init__(self, storage_service: StorageService, staging_root: str | Path) -> None:
        self._storage_service = storage_service
        self._staging_root = Path(staging_root).resolve() / ".pending"
        self._staging_root.mkdir(parents=True, exist_ok=True)
        self._lock = RLock()

    def save(self, media: DownloadedMedia, sender: str) -> None:
        with self._lock:
            staging_path = self._staging_path_for(media.message_id)
            staging_path.write_bytes(media.content)
            self._storage_service.save_pending_media(
                message_id=media.message_id,
                sender=sender,
                file_name=media.file_name,
                mimetype=media.mimetype,
                size_bytes=media.size_bytes,
                staging_path=str(staging_path),
                created_at=time.time(),
            )

    def get(self, message_id: str) -> DownloadedMedia | None:
        row = self._storage_service.get_pending_media(message_id)
        if row is None:
            return None

        staging_path = Path(str(row["staging_path"]))
        if not staging_path.is_file():
            return None

        return DownloadedMedia(
            message_id=str(row["message_id"]),
            content=staging_path.read_bytes(),
            mimetype=str(row["mimetype"]),
            size_bytes=int(row["size_bytes"]),
            file_name=str(row["file_name"]) if row.get("file_name") is not None else None,
        )

    def delete(self, message_id: str) -> None:
        with self._lock:
            row = self._storage_service.get_pending_media(message_id)
            if row is not None:
                Path(str(row["staging_path"])).unlink(missing_ok=True)
            self._storage_service.delete_pending_media(message_id)

    def purge_older_than(self, cutoff_epoch: float) -> int:
        with self._lock:
            for row in self._storage_service.list_pending_media_before(cutoff_epoch):
                Path(str(row["staging_path"])).unlink(missing_ok=True)
            return self._storage_service.delete_pending_media_before(cutoff_epoch)

    def _staging_path_for(self, message_id: str) -> Path:
        digest = hashlib.sha1(message_id.encode("utf-8")).hexdigest()
        return self._staging_root / f"{digest}.bin"
