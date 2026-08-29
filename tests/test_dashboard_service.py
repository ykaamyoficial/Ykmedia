import asyncio
from pathlib import Path

from app.services.dashboard_service import DashboardService
from app.services.storage_service import StorageService


class OnlineEvolutionClient:
    async def health(self) -> dict[str, object]:
        return {"status": "ok"}

    async def get_connection_state(self) -> dict[str, object]:
        return {"instance": {"state": "open"}}


class OfflineEvolutionClient:
    async def health(self) -> dict[str, object]:
        raise RuntimeError("offline")

    async def get_connection_state(self) -> dict[str, object]:
        return {}


def test_dashboard_service_returns_real_storage_metrics(tmp_path: Path) -> None:
    media_root = tmp_path / "media"
    media_root.mkdir()
    stored_file = media_root / "Louvores" / "arquivo.mp3"
    stored_file.parent.mkdir()
    stored_file.write_bytes(b"audio")
    storage = StorageService(database_path=tmp_path / "ykmedia.sqlite3")
    storage.replace_categories(["Louvores", "Mensagens"])
    storage.save_processing_job(
        job_id="job-1",
        sender="556299999999@s.whatsapp.net",
        origin="WhatsApp",
        created_at="2026-07-29T10:00:00+00:00",
        status="PENDENTE",
        payload={"ok": True},
    )
    storage.save_media_history(
        history_id="hist-1",
        date="2026-07-29T10:01:00+00:00",
        sender="556299999999@s.whatsapp.net",
        origin="WhatsApp",
        category="Louvores",
        final_name="arquivo.mp3",
        file_path=str(Path("Louvores") / "arquivo.mp3"),
        status="CONCLUIDO",
    )
    storage.save_conversation_message(
        record_id="msg-1",
        message_id="MSG1",
        sender="556299999999@s.whatsapp.net",
        direction="incoming",
        content="Arquivo recebido",
        message_type="image",
        state=None,
        media_id="MSG1",
        created_at="2026-07-29T10:02:00+00:00",
        status="CONCLUIDO",
    )

    service = DashboardService(
        storage_service=storage,
        evolution_client=OnlineEvolutionClient(),
        media_root=media_root,
    )

    overview = asyncio.run(service.get_overview())

    assert overview.system.backend_online is True
    assert overview.system.database_connected is True
    assert overview.evolution.online is True
    assert overview.whatsapp.connected is True
    assert overview.downloads.queue == 1
    assert overview.files.stored_count == 1
    assert overview.files.storage_used_bytes == 5
    assert overview.files.categories == ["Louvores", "Mensagens"]
    assert overview.conversations.total == 1
    assert overview.history[0].final_name == "arquivo.mp3"


def test_blocking_snapshot_is_collected_without_an_event_loop(tmp_path: Path) -> None:
    # A parte sincrona (SQLite + disco) deve rodar fora do event loop.
    storage = StorageService(database_path=tmp_path / "ykmedia.sqlite3")
    storage.replace_categories(["Louvores"])
    service = DashboardService(
        storage_service=storage,
        evolution_client=OfflineEvolutionClient(),
        media_root=tmp_path / "media",
    )

    snapshot = service._collect_blocking_snapshot()

    assert snapshot.database_connected is True
    assert snapshot.storage_ready is False
    assert snapshot.files.categories == ["Louvores"]


def test_dashboard_service_marks_evolution_offline_without_breaking(tmp_path: Path) -> None:
    storage = StorageService(database_path=tmp_path / "ykmedia.sqlite3")
    service = DashboardService(
        storage_service=storage,
        evolution_client=OfflineEvolutionClient(),
        media_root=tmp_path / "media",
    )

    overview = asyncio.run(service.get_overview())

    assert overview.evolution.online is False
    assert overview.whatsapp.connected is False
    assert overview.whatsapp.qr_pending is True
    assert overview.health[2].status == "offline"
