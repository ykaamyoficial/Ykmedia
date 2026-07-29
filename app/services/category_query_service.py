from pathlib import Path

from app.core.config import settings
from app.models.categories import CategoriesResponse, CategoryItem
from app.services.category_service import CategoryService


class CategoryQueryService:
    def __init__(self, category_service: CategoryService) -> None:
        self._category_service = category_service

    def list_categories(self) -> CategoriesResponse:
        categories = self._category_service.list_categories()
        items = [
            CategoryItem(
                position=index,
                name=category,
                folder=str(Path(settings.FILE_STORAGE_ROOT).resolve() / category),
            )
            for index, category in enumerate(categories, start=1)
        ]
        return CategoriesResponse(items=items, total=len(items))

    def save_categories(self, categories: list[str]) -> CategoriesResponse:
        current = self._category_service.list_categories()

        for category in current:
            if category not in categories:
                self._category_service.remove(category)

        for category in categories:
            if category not in self._category_service.list_categories():
                self._category_service.add(category)

        self._category_service.reorder(categories)
        return self.list_categories()
