from fastapi.testclient import TestClient
from app.core.config import settings
from app.main import app, create_app

client = TestClient(app)


def test_health() -> None:
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_tauri_origin_is_allowed_to_access_backend_with_legacy_configuration(monkeypatch) -> None:
    monkeypatch.setattr(
        settings,
        "FRONTEND_CORS_ORIGINS",
        "http://127.0.0.1:5173,http://localhost:5173,tauri://localhost",
    )
    response = TestClient(create_app()).get(
        "/health",
        headers={"Origin": "http://tauri.localhost"},
    )

    assert response.status_code == 200
    assert response.headers["access-control-allow-origin"] == "http://tauri.localhost"
