from pathlib import Path

from app.services.history_query_service import HistoryQueryService
from app.services.storage_service import StorageService


def test_history_query_service_lists_media_history_like_desktop(tmp_path: Path) -> None:
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

    response = HistoryQueryService(storage).list_history()

    assert response.total == 1
    assert response.items[0].date_display == "29/07/2026 10:00"
    assert response.items[0].sender == "+55 62 99999-9999"
    assert response.items[0].origin == "WhatsApp"
    assert response.items[0].category == "Louvores"
    assert response.items[0].final_name == "imagem.jpg"
    assert response.items[0].kind == "Imagem"
    assert response.items[0].status == "CONCLUIDO"


def test_history_query_service_detects_youtube_kind(tmp_path: Path) -> None:
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

    item = HistoryQueryService(storage).list_history().items[0]

    assert item.kind == "YouTube"
