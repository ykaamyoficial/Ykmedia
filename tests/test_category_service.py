import pytest

from app.services.category_service import (
    CategoryAlreadyExistsError,
    CategoryNotFoundError,
    CategoryService,
    InvalidCategoryOrderError,
)


def test_default_categories() -> None:
    service = CategoryService()

    assert service.list_categories() == ["Louvores", "Mensagens", "Jovens", "Criancas", "Outros"]
    assert service.format_options() == "1 Louvores, 2 Mensagens, 3 Jovens, 4 Criancas, 5 Outros"


def test_add_category() -> None:
    service = CategoryService()

    service.add("Eventos")

    assert service.list_categories() == [
        "Louvores",
        "Mensagens",
        "Jovens",
        "Criancas",
        "Outros",
        "Eventos",
    ]


def test_rejects_duplicate_category() -> None:
    service = CategoryService()

    with pytest.raises(CategoryAlreadyExistsError):
        service.add("Louvores")


def test_remove_category() -> None:
    service = CategoryService()

    service.remove("Jovens")

    assert service.list_categories() == ["Louvores", "Mensagens", "Criancas", "Outros"]


def test_rejects_removing_missing_category() -> None:
    service = CategoryService()

    with pytest.raises(CategoryNotFoundError):
        service.remove("Eventos")


def test_reorder_categories() -> None:
    service = CategoryService(categories=["A", "B", "C"])

    service.reorder(["C", "A", "B"])

    assert service.list_categories() == ["C", "A", "B"]
    assert service.get_by_option("1") == "C"


def test_rejects_invalid_reorder() -> None:
    service = CategoryService(categories=["A", "B", "C"])

    with pytest.raises(InvalidCategoryOrderError):
        service.reorder(["A", "B"])
