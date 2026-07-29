from fastapi.testclient import TestClient

from app.main import app
from app.models.dashboard import DashboardOverview
from app.services.application_factory import get_dashboard_service


class FakeDashboardService:
    async def get_overview(self) -> DashboardOverview:
        return DashboardOverview(
            generated_at="2026-07-29T10:00:00+00:00",
            system={
                "version": "0.1.0",
                "uptime_seconds": 10,
                "backend_online": True,
                "database_connected": True,
            },
            evolution={
                "online": True,
                "instance": "ykmedia",
                "last_sync": "2026-07-29T10:00:00+00:00",
            },
            whatsapp={
                "status": "connected",
                "connected": True,
                "qr_pending": False,
            },
            downloads={
                "in_progress": 0,
                "completed": 1,
                "failures": 0,
                "queue": 0,
            },
            files={
                "stored_count": 1,
                "storage_used_bytes": 5,
                "categories": ["Louvores"],
            },
            conversations={
                "total": 1,
                "active_contacts": 0,
                "latest_messages": [],
            },
            history=[],
            health=[],
            has_data=True,
        )


def test_dashboard_overview_endpoint() -> None:
    app.dependency_overrides[get_dashboard_service] = lambda: FakeDashboardService()
    try:
        response = TestClient(app).get("/dashboard/overview")
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    body = response.json()
    assert body["system"]["backend_online"] is True
    assert body["evolution"]["instance"] == "ykmedia"
    assert body["files"]["stored_count"] == 1
