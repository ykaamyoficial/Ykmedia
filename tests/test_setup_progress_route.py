"""A tela acompanha o preparo por esta rota enquanto o POST /prepare corre."""

from fastapi.testclient import TestClient

from app.core.config import settings
from app.main import create_app
from app.services.application_factory import get_setup_progress_store
from app.services.configuration_manager import SetupStepResult, SetupStepStatus
from app.services.setup_progress import SetupProgressStore


def _client(store: SetupProgressStore) -> TestClient:
    app = create_app()
    app.dependency_overrides[get_setup_progress_store] = lambda: store
    return TestClient(app)


def test_progress_is_empty_before_any_preparation(monkeypatch) -> None:
    monkeypatch.setattr(settings, "API_AUTH_TOKEN", "")

    response = _client(SetupProgressStore()).get("/settings/prepare/status")

    assert response.status_code == 200
    assert response.json()["running"] is False
    assert response.json()["steps"] == []


def test_progress_shows_the_step_in_flight(monkeypatch) -> None:
    monkeypatch.setattr(settings, "API_AUTH_TOKEN", "")
    store = SetupProgressStore()
    store.start([("config", "Configuracao"), ("environment", "Ambiente")])
    store.record(SetupStepResult("config", "Configuracao", SetupStepStatus.OK, "pronto"))
    store.mark_running("environment")

    body = _client(store).get("/settings/prepare/status").json()

    assert body["running"] is True
    assert [step["status"] for step in body["steps"]] == ["OK", "RUNNING"]


def test_progress_requires_the_api_token(monkeypatch) -> None:
    monkeypatch.setattr(settings, "API_AUTH_TOKEN", "segredo-local")

    response = _client(SetupProgressStore()).get("/settings/prepare/status")

    assert response.status_code == 401
