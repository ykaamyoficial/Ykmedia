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


def test_preflight_allows_the_authorization_header() -> None:
    """A interface envia o token da API em Authorization.

    Sem esse header liberado no CORS o navegador barra toda requisicao e o app
    aparece como "Backend offline" — falha que so acontece no app empacotado,
    porque em desenvolvimento o token fica vazio e o header nao e enviado.
    """
    response = TestClient(create_app()).options(
        "/health",
        headers={
            "Origin": "http://tauri.localhost",
            "Access-Control-Request-Method": "GET",
            "Access-Control-Request-Headers": "authorization",
        },
    )

    assert response.status_code == 200
    allowed = response.headers["access-control-allow-headers"].lower()
    assert "authorization" in allowed


def test_preflight_allows_a_real_api_call() -> None:
    response = TestClient(create_app()).options(
        "/settings/evolution/license",
        headers={
            "Origin": "http://tauri.localhost",
            "Access-Control-Request-Method": "GET",
            "Access-Control-Request-Headers": "authorization,content-type",
        },
    )

    assert response.status_code == 200
