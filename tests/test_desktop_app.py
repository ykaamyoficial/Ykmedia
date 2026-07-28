import os
import sys
from pathlib import Path

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtWidgets import QApplication

from app.desktop.data_provider import DesktopDataProvider
from app.desktop.main_window import YkMediaMainWindow
from app.services.category_service import CategoryService
from app.services.processing_queue import ProcessingJobOrigin, ProcessingQueue
from app.services.storage_service import StorageService


class FakeEvolutionClient:
    def __init__(self) -> None:
        self.calls: list[str] = []

    async def get_connection_state(self) -> dict[str, object]:
        self.calls.append("state")
        return {"instance": {"state": "open"}}

    async def connect_instance(self) -> dict[str, object]:
        self.calls.append("connect")
        return {
            "instance": {"state": "connecting"},
            "qrcode": {"base64": "data:image/png;base64,abc"},
        }

    async def logout_instance(self) -> dict[str, object]:
        self.calls.append("logout")
        return {"instance": {"state": "close"}}


def _application() -> QApplication:
    application = QApplication.instance()
    if application is None:
        application = QApplication(sys.argv)

    return application


def _provider(tmp_path: Path) -> DesktopDataProvider:
    storage_service = StorageService(database_path=tmp_path / "ykmedia.sqlite3")
    processing_queue = ProcessingQueue()
    processing_queue.enqueue(
        sender="556299999999@s.whatsapp.net",
        origin=ProcessingJobOrigin.WHATSAPP,
        payload={"event": "messages.upsert"},
    )
    storage_service.save_media_history(
        history_id="hist-1",
        date="2026-07-27T17:21:35+00:00",
        sender="556299999999@s.whatsapp.net",
        origin="WhatsApp",
        category="Louvores",
        final_name="louvor.mp3",
        file_path="Louvores/louvor.mp3",
        status="CONCLUIDO",
    )
    storage_service.save_session(
        sender_id="556288888888@s.whatsapp.net",
        state="WAITING_CATEGORY",
        category=None,
        filename=None,
        updated_at=1785198927.0,
    )
    return DesktopDataProvider(
        storage_service=storage_service,
        processing_queue=processing_queue,
        category_service=CategoryService(),
        evolution_client=FakeEvolutionClient(),
    )


def test_desktop_application_initializes(tmp_path: Path) -> None:
    _application()

    window = YkMediaMainWindow(data_provider=_provider(tmp_path))

    assert window.windowTitle() == "YkMedia"


def test_desktop_loads_required_tabs(tmp_path: Path) -> None:
    _application()

    window = YkMediaMainWindow(data_provider=_provider(tmp_path))

    assert list(window.pages) == [
        "Dashboard",
        "Fila",
        "Historico",
        "Conversas",
        "Categorias",
        "Configuracoes",
        "Logs",
        "Sobre",
    ]
    assert len(window.nav_buttons) == 8


def test_desktop_loads_queue_and_history_data(tmp_path: Path) -> None:
    _application()

    window = YkMediaMainWindow(data_provider=_provider(tmp_path))
    window.refresh_all()

    assert window.queue_table.rowCount() == 1
    assert window.history_table.rowCount() == 1


def test_desktop_sidebar_navigation_changes_content(tmp_path: Path) -> None:
    _application()

    window = YkMediaMainWindow(data_provider=_provider(tmp_path))
    window.nav_buttons["Fila"].click()

    assert window.header_title.text() == "Fila"
    assert window.content_stack.currentWidget() is window.pages["Fila"]


def test_desktop_filters_queue_rows(tmp_path: Path) -> None:
    _application()
    window = YkMediaMainWindow(data_provider=_provider(tmp_path))

    window.queue_search.setText("nao existe")

    assert window.queue_table.rowCount() == 0


def test_desktop_updates_history_filter_from_categories(tmp_path: Path) -> None:
    _application()
    window = YkMediaMainWindow(data_provider=_provider(tmp_path))

    window.category_input.setText("Eventos")
    window._add_category()

    assert window.history_filter.findText("Eventos") >= 0


def test_data_provider_deletes_conversation(tmp_path: Path) -> None:
    provider = _provider(tmp_path)
    conversations = provider.list_conversations()

    provider.delete_conversation(conversations[0]["sender"])

    assert provider.list_conversations() == []


def test_data_provider_exports_logs(tmp_path: Path, monkeypatch) -> None:
    provider = _provider(tmp_path)
    monkeypatch.setattr(provider, "_read_log_lines", lambda: ["INFO: teste", "ERROR: falha"])
    target_path = tmp_path / "logs.txt"

    count = provider.export_logs(target_path)

    assert count == 2
    assert "ERROR" in target_path.read_text(encoding="utf-8")


def test_data_provider_reads_evolution_session_state(tmp_path: Path) -> None:
    provider = _provider(tmp_path)

    snapshot = provider.get_evolution_session_snapshot()

    assert snapshot.instance_name == "ykmedia"
    assert snapshot.state == "open"


def test_data_provider_requests_qrcode(tmp_path: Path) -> None:
    provider = _provider(tmp_path)

    snapshot = provider.connect_evolution_session()

    assert snapshot.state == "connecting"
    assert snapshot.qrcode_base64 == "data:image/png;base64,abc"


def test_data_provider_disconnects_evolution_session(tmp_path: Path) -> None:
    provider = _provider(tmp_path)

    snapshot = provider.disconnect_evolution_session()

    assert snapshot.state == "close"


def test_data_provider_reconnects_evolution_session_with_logout_first(tmp_path: Path) -> None:
    storage_service = StorageService(database_path=tmp_path / "ykmedia.sqlite3")
    evolution_client = FakeEvolutionClient()
    provider = DesktopDataProvider(
        storage_service=storage_service,
        processing_queue=ProcessingQueue(),
        category_service=CategoryService(),
        evolution_client=evolution_client,
    )

    snapshot = provider.reconnect_evolution_session()

    assert snapshot.state == "connecting"
    assert snapshot.qrcode_base64 == "data:image/png;base64,abc"
    assert evolution_client.calls == ["logout", "connect"]
