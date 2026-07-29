from pathlib import Path

from app.core.config import settings
from app.services.category_query_service import CategoryQueryService
from app.services.category_service import CategoryService
from app.services.storage_service import StorageService


def test_category_query_service_lists_categories_with_positions_and_folders(tmp_path: Path) -> None:
    previous_root = settings.FILE_STORAGE_ROOT
    settings.FILE_STORAGE_ROOT = str(tmp_path / "media")
    storage = StorageService(database_path=tmp_path / "ykmedia.sqlite3")
    service = CategoryQueryService(CategoryService(categories=["Louvores", "Mensagens"], storage_service=storage))

    try:
        response = service.list_categories()
    finally:
        settings.FILE_STORAGE_ROOT = previous_root

    assert response.total == 2
    assert response.items[0].position == 1
    assert response.items[0].name == "Louvores"
    assert response.items[0].folder.endswith("media\\Louvores") or response.items[0].folder.endswith("media/Louvores")


def test_category_query_service_saves_category_list_like_desktop(tmp_path: Path) -> None:
    storage = StorageService(database_path=tmp_path / "ykmedia.sqlite3")
    category_service = CategoryService(categories=["Louvores", "Mensagens"], storage_service=storage)
    service = CategoryQueryService(category_service)

    response = service.save_categories(["Mensagens", "Jovens"])

    assert [item.name for item in response.items] == ["Mensagens", "Jovens"]
    assert category_service.list_categories() == ["Mensagens", "Jovens"]
