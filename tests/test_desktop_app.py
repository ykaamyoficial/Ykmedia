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
    return DesktopDataProvider(
        storage_service=storage_service,
        processing_queue=processing_queue,
        category_service=CategoryService(),
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
