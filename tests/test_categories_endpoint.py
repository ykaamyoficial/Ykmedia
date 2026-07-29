from fastapi.testclient import TestClient

from app.main import app
from app.models.categories import CategoriesResponse
from app.services.application_factory import get_category_query_service


class FakeCategoryQueryService:
    def __init__(self) -> None:
        self.categories = ["Louvores"]

    def list_categories(self) -> CategoriesResponse:
        return CategoriesResponse(
            items=[{"position": 1, "name": self.categories[0], "folder": "C:\\media\\Louvores"}],
            total=1,
        )

    def save_categories(self, categories: list[str]) -> CategoriesResponse:
        self.categories = categories
        return CategoriesResponse(
            items=[
                {"position": index, "name": category, "folder": f"C:\\media\\{category}"}
                for index, category in enumerate(categories, start=1)
            ],
            total=len(categories),
        )


def test_list_categories_endpoint() -> None:
    fake = FakeCategoryQueryService()
    app.dependency_overrides[get_category_query_service] = lambda: fake
    try:
        response = TestClient(app).get("/categories")
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    assert response.json()["items"][0]["name"] == "Louvores"


def test_save_categories_endpoint() -> None:
    fake = FakeCategoryQueryService()
    app.dependency_overrides[get_category_query_service] = lambda: fake
    try:
        response = TestClient(app).put("/categories", json={"categories": ["Mensagens", "Jovens"]})
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    assert [item["name"] for item in response.json()["items"]] == ["Mensagens", "Jovens"]
