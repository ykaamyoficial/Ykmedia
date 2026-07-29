from fastapi.testclient import TestClient

from app.main import app
from app.models.files import FileLibraryResponse
from app.services.application_factory import get_file_query_service


class FakeFileQueryService:
    def list_files(self) -> FileLibraryResponse:
        return FileLibraryResponse(
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
                    "absolute_path": "C:\\media\\Louvores\\imagem.jpg",
                    "kind": "Imagem",
                    "status": "CONCLUIDO",
                    "size": "5 B",
                    "exists": True,
                }
            ],
            total=1,
        )


def test_list_files_endpoint() -> None:
    app.dependency_overrides[get_file_query_service] = lambda: FakeFileQueryService()
    try:
        response = TestClient(app).get("/files")
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    assert response.json()["items"][0]["final_name"] == "imagem.jpg"
