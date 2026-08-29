import time
from pathlib import Path

from app.models.download import DownloadedMedia
from app.models.persistence import MediaRecord
from app.repositories.media_repository import SQLiteMediaRepository
from app.repositories.pending_media_repository import SQLitePendingMediaRepository
from app.services.storage_service import StorageService


def _media(message_id: str = "MSG1") -> DownloadedMedia:
    return DownloadedMedia(
        message_id=message_id,
        content=b"file-bytes-" + message_id.encode(),
        mimetype="image/jpeg",
        size_bytes=21,
        file_name=f"{message_id}.jpg",
    )


def test_pending_media_survives_a_new_repository_instance(tmp_path: Path) -> None:
    database_path = tmp_path / "ykmedia.sqlite3"
    staging_root = tmp_path / "media"

    first = SQLitePendingMediaRepository(StorageService(database_path), staging_root)
    first.save(_media(), sender="5562@s.whatsapp.net")

    # Simula reinicio do backend: nova instancia, mesmo banco/disco.
    second = SQLitePendingMediaRepository(StorageService(database_path), staging_root)
    restored = second.get("MSG1")

    assert restored is not None
    assert restored.content == b"file-bytes-MSG1"
    assert restored.file_name == "MSG1.jpg"
    assert restored.mimetype == "image/jpeg"


def test_pending_media_delete_removes_row_and_file(tmp_path: Path) -> None:
    repo = SQLitePendingMediaRepository(StorageService(tmp_path / "db.sqlite3"), tmp_path / "media")
    repo.save(_media(), sender="5562@s.whatsapp.net")

    repo.delete("MSG1")

    assert repo.get("MSG1") is None
    assert list((tmp_path / "media" / ".pending").glob("*.bin")) == []


def test_pending_media_purge_older_than(tmp_path: Path) -> None:
    storage = StorageService(tmp_path / "db.sqlite3")
    repo = SQLitePendingMediaRepository(storage, tmp_path / "media")
    repo.save(_media("OLD"), sender="a")
    repo.save(_media("NEW"), sender="a")
    # Envelhece o registro OLD diretamente no banco.
    storage.save_pending_media(
        message_id="OLD",
        sender="a",
        file_name="OLD.jpg",
        mimetype="image/jpeg",
        size_bytes=21,
        staging_path=str(tmp_path / "media" / ".pending" / _staging_name("OLD")),
        created_at=time.time() - 10_000,
    )

    removed = repo.purge_older_than(time.time() - 5_000)

    assert removed == 1
    assert repo.get("OLD") is None
    assert repo.get("NEW") is not None


def test_sqlite_media_repository_round_trip(tmp_path: Path) -> None:
    repo = SQLiteMediaRepository(StorageService(tmp_path / "db.sqlite3"))
    record = MediaRecord(
        media_id="m1",
        message_id="MSG1",
        file_name="foto.jpg",
        relative_path="Louvores/foto.jpg",
        mimetype="image/jpeg",
        size_bytes=10,
        sha256="deadbeef",
        absolute_path=str(tmp_path / "foto.jpg"),
    )

    repo.save(record)

    assert repo.exists("m1") is True
    assert repo.get_by_id("m1") == record
    assert repo.list() == [record]

    repo.delete("m1")
    assert repo.get_by_id("m1") is None


def _staging_name(message_id: str) -> str:
    import hashlib

    return f"{hashlib.sha1(message_id.encode()).hexdigest()}.bin"
