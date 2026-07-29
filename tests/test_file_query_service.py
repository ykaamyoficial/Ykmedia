from pathlib import Path

from app.core.config import settings
from app.services.file_query_service import FileQueryService
from app.services.storage_service import StorageService


def test_file_query_service_lists_media_history_as_files(tmp_path: Path) -> None:
    previous_root = settings.FILE_STORAGE_ROOT
    settings.FILE_STORAGE_ROOT = str(tmp_path)
    media_file = tmp_path / "Louvores" / "imagem.jpg"
    media_file.parent.mkdir(parents=True)
    media_file.write_bytes(b"image")
    storage = StorageService(database_path=tmp_path / "ykmedia.sqlite3")
    storage.save_media_history(
        history_id="hist-1",
        date="2026-07-29T10:00:00+00:00",
        sender="5562999999999@s.whatsapp.net",
        origin="WhatsApp",
        category="Louvores",
        final_name="imagem.jpg",
        file_path=str(Path("Louvores") / "imagem.jpg"),
        status="CONCLUIDO",
    )

    try:
        response = FileQueryService(storage).list_files()
    finally:
        settings.FILE_STORAGE_ROOT = previous_root

    assert response.total == 1
    assert response.items[0].sender == "+55 62 99999-9999"
    assert response.items[0].kind == "Imagem"
    assert response.items[0].size == "5 B"
    assert response.items[0].exists is True


def test_file_query_service_marks_missing_file(tmp_path: Path) -> None:
    previous_root = settings.FILE_STORAGE_ROOT
    settings.FILE_STORAGE_ROOT = str(tmp_path)
    storage = StorageService(database_path=tmp_path / "ykmedia.sqlite3")
    storage.save_media_history(
        history_id="hist-1",
        date="2026-07-29T10:00:00+00:00",
        sender="5562999999999@s.whatsapp.net",
        origin="YouTube",
        category="Louvores",
        final_name="video.mp4",
        file_path=str(Path("Louvores") / "video.mp4"),
        status="CONCLUIDO",
    )

    try:
        item = FileQueryService(storage).list_files().items[0]
    finally:
        settings.FILE_STORAGE_ROOT = previous_root

    assert item.kind == "YouTube"
    assert item.exists is False
    assert item.size == "Tamanho indisponivel"
