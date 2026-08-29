from app.services.category_service import CategoryService
from app.services.interactive_menu_builder import InteractiveMenuBuilder


def test_builds_button_sized_menu_with_three_options() -> None:
    builder = InteractiveMenuBuilder()
    service = CategoryService(categories=["Louvores", "Mensagens", "Jovens"])

    prompt = builder.build_category_menu(service)

    assert len(prompt.options) == 3
    assert [option.id for option in prompt.options] == ["category:1", "category:2", "category:3"]
    assert prompt.button_text == "Ver categorias"


def test_builds_list_sized_menu_with_four_or_more_options() -> None:
    builder = InteractiveMenuBuilder()
    service = CategoryService(categories=["A", "B", "C", "D"])

    prompt = builder.build_category_menu(service)

    assert len(prompt.options) == 4
    assert prompt.options[3].id == "category:4"


def test_paginates_categories_when_limit_is_exceeded() -> None:
    builder = InteractiveMenuBuilder()
    service = CategoryService(categories=[f"Categoria {index}" for index in range(1, 12)])

    first_page = builder.build_category_menu(service)
    second_page = builder.build_category_menu(service, page=2)

    assert first_page.options[-1].id == "action:next_page:2"
    assert second_page.options[0].id == "category:11"
    assert second_page.options[-1].id == "action:previous_page:1"


def test_shortens_long_category_titles_without_changing_description() -> None:
    builder = InteractiveMenuBuilder()
    service = CategoryService(categories=["Categoria muito grande para botao"])

    prompt = builder.build_category_menu(service)

    assert prompt.options[0].title.endswith("...")
    assert prompt.options[0].description == "Categoria muito grande para botao"
