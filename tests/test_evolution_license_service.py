import httpx
import pytest

from app.services.evolution_license_service import EvolutionLicenseService, LicenseStatus


def _service(monkeypatch, handler) -> EvolutionLicenseService:
    """Injeta um transporte falso no httpx.get usado pelo servico."""

    def fake_get(url, headers=None, timeout=None):
        request = httpx.Request("GET", url, headers=headers)
        return handler(request)

    monkeypatch.setattr(httpx, "get", fake_get)
    return EvolutionLicenseService(base_url="http://evolution.test", api_key="k")


def test_status_reports_active(monkeypatch) -> None:
    service = _service(
        monkeypatch,
        lambda request: httpx.Response(200, json={"status": "active"}, request=request),
    )

    assert service.status().status is LicenseStatus.ACTIVE


def test_status_reports_pending(monkeypatch) -> None:
    service = _service(
        monkeypatch,
        lambda request: httpx.Response(200, json={"status": "inactive"}, request=request),
    )

    assert service.status().status is LicenseStatus.PENDING


def test_status_detects_versions_without_licensing(monkeypatch) -> None:
    # A v2.3.7 nao tem as rotas /license: nao faz sentido pedir ativacao.
    service = _service(
        monkeypatch,
        lambda request: httpx.Response(404, json={"status": 404, "error": "Not Found"}, request=request),
    )

    assert service.status().status is LicenseStatus.NOT_REQUIRED


def test_status_survives_evolution_being_down(monkeypatch) -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        raise httpx.ConnectError("offline", request=request)

    service = _service(monkeypatch, handler)

    assert service.status().status is LicenseStatus.UNAVAILABLE


def test_registration_sends_redirect_uri_and_returns_url(monkeypatch) -> None:
    captured: dict[str, str] = {}

    def handler(request: httpx.Request) -> httpx.Response:
        captured["url"] = str(request.url)
        return httpx.Response(
            200,
            json={"status": "pending", "register_url": "https://license.test/register?token=abc"},
            request=request,
        )

    service = _service(monkeypatch, handler)
    state = service.start_registration()

    # O redirect_uri e o que faz a instancia se ativar sozinha ao fim do cadastro.
    assert "redirect_uri=" in captured["url"]
    assert "license%2Factivate" in captured["url"]
    assert state.status is LicenseStatus.PENDING
    assert state.register_url == "https://license.test/register?token=abc"


def test_activate_exchanges_code(monkeypatch) -> None:
    captured: dict[str, str] = {}

    def handler(request: httpx.Request) -> httpx.Response:
        captured["url"] = str(request.url)
        return httpx.Response(200, json={"status": "active"}, request=request)

    service = _service(monkeypatch, handler)
    state = service.activate("CODE-123")

    assert "code=CODE-123" in captured["url"]
    assert state.status is LicenseStatus.ACTIVE


def test_activate_reports_invalid_code(monkeypatch) -> None:
    service = _service(
        monkeypatch,
        lambda request: httpx.Response(
            400,
            json={"error": "Invalid or expired code", "details": "expired"},
            request=request,
        ),
    )
    state = service.activate("VELHO")

    assert state.status is LicenseStatus.PENDING
    assert "expired" in state.message


@pytest.mark.parametrize("payload", [[], "texto", None])
def test_unexpected_payloads_do_not_crash(monkeypatch, payload) -> None:
    service = _service(
        monkeypatch,
        lambda request: httpx.Response(200, json=payload, request=request),
    )

    assert service.status().status is LicenseStatus.UNAVAILABLE
