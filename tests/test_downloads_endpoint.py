from fastapi.testclient import TestClient

from app.main import app
from app.models.downloads import ClearCompletedDownloadsResponse, DownloadJobsResponse
from app.services.application_factory import get_download_query_service


class FakeDownloadQueryService:
    def list_jobs(self) -> DownloadJobsResponse:
        return DownloadJobsResponse(
            items=[
                {
                    "id": "job-123456",
                    "short_id": "job-1234",
                    "sender": "+55 62 99999-9999",
                    "sender_raw": "5562999999999@s.whatsapp.net",
                    "origin": "WhatsApp",
                    "file": "foto.jpg",
                    "kind": "Imagem",
                    "status": "PENDENTE",
                    "created_at": "29/07/2026 10:00",
                }
            ],
            total=1,
        )

    def clear_completed(self) -> ClearCompletedDownloadsResponse:
        return ClearCompletedDownloadsResponse(removed=2)


def test_list_download_jobs_endpoint() -> None:
    app.dependency_overrides[get_download_query_service] = lambda: FakeDownloadQueryService()
    try:
        response = TestClient(app).get("/downloads/jobs")
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    assert response.json()["items"][0]["file"] == "foto.jpg"


def test_clear_completed_download_jobs_endpoint() -> None:
    app.dependency_overrides[get_download_query_service] = lambda: FakeDownloadQueryService()
    try:
        response = TestClient(app).delete("/downloads/jobs/completed")
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    assert response.json()["removed"] == 2
