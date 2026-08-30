from fastapi.testclient import TestClient

from app.core.config import settings
from app.main import create_app
from app.models.categories import CategoriesResponse
from app.services.application_factory import get_category_query_service


class _FakeCategoryQueryService:
    def list_categories(self) -> CategoriesResponse:
        return CategoriesResponse(items=[], total=0)


def _client() -> TestClient:
    app = create_app()
    app.dependency_overrides[get_category_query_service] = _FakeCategoryQueryService
    return TestClient(app)


def test_protected_route_is_open_when_token_not_configured(monkeypatch) -> None:
    monkeypatch.setattr(settings, "API_AUTH_TOKEN", "")
    response = _client().get("/categories")
    assert response.status_code == 200


def test_protected_route_rejects_missing_token(monkeypatch) -> None:
    monkeypatch.setattr(settings, "API_AUTH_TOKEN", "segredo-local")
    response = _client().get("/categories")
    assert response.status_code == 401


def test_protected_route_rejects_wrong_token(monkeypatch) -> None:
    monkeypatch.setattr(settings, "API_AUTH_TOKEN", "segredo-local")
    response = _client().get("/categories", headers={"Authorization": "Bearer errado"})
    assert response.status_code == 401


def test_protected_route_accepts_valid_token(monkeypatch) -> None:
    monkeypatch.setattr(settings, "API_AUTH_TOKEN", "segredo-local")
    response = _client().get(
        "/categories",
        headers={"Authorization": "Bearer segredo-local"},
    )
    assert response.status_code == 200


def test_health_and_webhook_stay_open_with_token_configured(monkeypatch) -> None:
    monkeypatch.setattr(settings, "API_AUTH_TOKEN", "segredo-local")
    client = _client()

    assert client.get("/health").status_code == 200
    # Webhook usa o proprio segredo (WEBHOOK_SECRET), nao o token de API.
    monkeypatch.setattr(settings, "WEBHOOK_SECRET", "")
    webhook_response = client.post("/webhooks/evolution", json={})
    assert webhook_response.status_code != 401


def test_prepare_requires_the_token_that_the_tauri_shell_must_send(monkeypatch) -> None:
    """Contrato com o shell Tauri.

    O app dispara /settings/prepare sozinho ao abrir. Quando o token passou a
    ser exigido, o shell continuou mandando a requisicao sem o cabecalho e
    recebia 401 — numa maquina nova isso significava que o Docker e a Evolution
    nunca subiam, sem nenhuma pista na interface.
    """
    monkeypatch.setattr(settings, "API_AUTH_TOKEN", "segredo-local")
    client = _client()

    assert client.post("/settings/prepare").status_code == 401
    assert (
        client.post(
            "/settings/prepare",
            headers={"Authorization": "Bearer segredo-local"},
        ).status_code
        != 401
    )
