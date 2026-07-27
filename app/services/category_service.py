from threading import RLock

from app.services.storage_service import StorageService


class CategoryServiceError(Exception):
    """Base exception for category service errors."""


class CategoryAlreadyExistsError(CategoryServiceError):
    """Raised when trying to add a duplicated category."""


class CategoryNotFoundError(CategoryServiceError):
    """Raised when trying to remove or move a missing category."""


class InvalidCategoryOrderError(CategoryServiceError):
    """Raised when category order does not match current categories."""


class CategoryService:
    _DEFAULT_CATEGORIES = ["Louvores", "Mensagens", "Jovens", "Criancas", "Outros"]

    def __init__(
        self,
        categories: list[str] | None = None,
        storage_service: StorageService | None = None,
    ) -> None:
        self._storage_service = storage_service
        stored_categories = self._storage_service.list_categories() if self._storage_service else []
        self._categories = list(categories or stored_categories or self._DEFAULT_CATEGORIES)
        self._lock = RLock()
        self._persist()

    def list_categories(self) -> list[str]:
        with self._lock:
            return list(self._categories)

    def get_by_option(self, option: str) -> str | None:
        try:
            index = int(option) - 1
        except ValueError:
            return None

        with self._lock:
            if index < 0 or index >= len(self._categories):
                return None

            return self._categories[index]

    def add(self, category: str) -> None:
        normalized_category = self._normalize(category)
        with self._lock:
            if normalized_category in self._categories:
                raise CategoryAlreadyExistsError("Categoria ja existe.")

            self._categories.append(normalized_category)
            self._persist()

    def remove(self, category: str) -> None:
        normalized_category = self._normalize(category)
        with self._lock:
            if normalized_category not in self._categories:
                raise CategoryNotFoundError("Categoria nao encontrada.")

            self._categories.remove(normalized_category)
            self._persist()

    def reorder(self, categories: list[str]) -> None:
        normalized_categories = [self._normalize(category) for category in categories]
        with self._lock:
            if set(normalized_categories) != set(self._categories) or len(normalized_categories) != len(
                self._categories
            ):
                raise InvalidCategoryOrderError("Ordem informada nao corresponde as categorias atuais.")

            self._categories = normalized_categories
            self._persist()

    def format_options(self) -> str:
        with self._lock:
            return ", ".join(
                f"{index} {category}"
                for index, category in enumerate(self._categories, start=1)
            )

    def _normalize(self, category: str) -> str:
        normalized_category = category.strip()
        if not normalized_category:
            raise ValueError("Categoria nao pode ser vazia.")

        return normalized_category

    def _persist(self) -> None:
        if self._storage_service is not None:
            self._storage_service.replace_categories(self._categories)
