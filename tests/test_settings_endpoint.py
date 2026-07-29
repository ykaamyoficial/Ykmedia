from fastapi.testclient import TestClient

from app.main import create_app
from app.models.settings import (
    AppSettingsResponse,
    DiagnosticReportResponse,
    EvolutionSessionResponse,
    SetupReportResponse,
)
from app.services.application_factory import get_settings_query_service


class FakeSettingsQueryService:
    def __init__(self) -> None:
        self.saved_payload: object | None = None

    def get_settings(self) -> AppSettingsResponse:
        return AppSettingsResponse(
            downloads_root="C:/YkMedia/Midias",
            ffmpeg_path="C:/ffmpeg/bin/ffmpeg.exe",
            sqlite_database="data/ykmedia.sqlite3",
            whatsapp_instance="ykmedia",
            evolution_state="open",
            evolution_message="Estado atualizado.",
        )

    def save_settings(self, request) -> AppSettingsResponse:
        self.saved_payload = request
        return self.get_settings()

    def get_evolution_session(self) -> EvolutionSessionResponse:
        return EvolutionSessionResponse(
            instance_name="ykmedia",
            state="open",
            message="Estado atualizado.",
        )

    def connect_evolution_session(self) -> EvolutionSessionResponse:
        return EvolutionSessionResponse(
            instance_name="ykmedia",
            state="connecting",
            message="QR Code solicitado.",
            qrcode_base64="base64",
        )

    def disconnect_evolution_session(self) -> EvolutionSessionResponse:
        return EvolutionSessionResponse(
            instance_name="ykmedia",
            state="close",
            message="Sessao desconectada.",
        )

    def run_diagnostics(self) -> DiagnosticReportResponse:
        return DiagnosticReportResponse(
            status="OK",
            message="Todos os componentes estao prontos.",
            items=[],
        )

    def prepare_system(self) -> SetupReportResponse:
        return SetupReportResponse(
            status="OK",
            message="Sistema pronto.",
            steps=[],
        )


def test_settings_endpoint_returns_current_settings() -> None:
    service = FakeSettingsQueryService()
    app = create_app()
    app.dependency_overrides[get_settings_query_service] = lambda: service

    response = TestClient(app).get("/settings")

    assert response.status_code == 200
    assert response.json()["downloads_root"] == "C:/YkMedia/Midias"


def test_settings_endpoint_saves_existing_fields() -> None:
    service = FakeSettingsQueryService()
    app = create_app()
    app.dependency_overrides[get_settings_query_service] = lambda: service

    response = TestClient(app).put(
        "/settings",
        json={
            "downloads_root": "D:/Midias",
            "ffmpeg_path": "D:/ffmpeg.exe",
            "sqlite_database": "data/test.sqlite3",
            "whatsapp_instance": "ykmedia",
        },
    )

    assert response.status_code == 200
    assert service.saved_payload.downloads_root == "D:/Midias"


def test_settings_endpoint_exposes_whatsapp_actions() -> None:
    service = FakeSettingsQueryService()
    app = create_app()
    app.dependency_overrides[get_settings_query_service] = lambda: service
    client = TestClient(app)

    assert client.get("/settings/evolution").json()["state"] == "open"
    assert client.post("/settings/evolution/connect").json()["qrcode_base64"] == "base64"
    assert client.post("/settings/evolution/disconnect").json()["state"] == "close"


def test_settings_endpoint_exposes_prepare_and_diagnostics() -> None:
    service = FakeSettingsQueryService()
    app = create_app()
    app.dependency_overrides[get_settings_query_service] = lambda: service
    client = TestClient(app)

    assert client.post("/settings/prepare").json()["message"] == "Sistema pronto."
    assert client.get("/settings/diagnostics").json()["status"] == "OK"
