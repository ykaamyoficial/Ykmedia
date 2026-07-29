from fastapi.testclient import TestClient

from app.main import app
from app.models.history import HistoryResponse
from app.services.application_factory import get_history_query_service


class FakeHistoryQueryService:
    def list_history(self) -> HistoryResponse:
        return HistoryResponse(
            items=[
                {
                    "id": "hist-1",
                    "date": "2026-07-29T10:00:00+00:00",
                    "date_display": "29/07/2026 10:00",
                    "sender": "+55 62 99999-9999",
                    "sender_raw": "5562999999999@s.whatsapp.net",
                    "origin": "WhatsApp",
                    "category": "Louvores",
                    "final_name": "imagem.jpg",
                    "file_path": "Louvores/imagem.jpg",
                    "kind": "Imagem",
                    "status": "CONCLUIDO",
                }
            ],
            total=1,
        )


def test_list_history_endpoint() -> None:
    app.dependency_overrides[get_history_query_service] = lambda: FakeHistoryQueryService()
    try:
        response = TestClient(app).get("/history")
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    assert response.json()["items"][0]["final_name"] == "imagem.jpg"
