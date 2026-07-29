from pathlib import Path

from app.services.contact_profile_service import ContactProfileService
from app.services.storage_service import StorageService


class FakeEvolutionClient:
    async def fetch_profile_picture_url(self, number: str) -> dict[str, object]:
        return {"profilePictureUrl": "https://example.com/photo.jpg"}


class FakeResponse:
    content = b"photo"

    def raise_for_status(self) -> None:
        return None


def test_contact_profile_service_caches_profile_photo(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setattr("app.services.contact_profile_service.httpx.get", lambda url, timeout: FakeResponse())
    storage = StorageService(database_path=tmp_path / "ykmedia.sqlite3")
    service = ContactProfileService(
        storage_service=storage,
        evolution_client=FakeEvolutionClient(),
        cache_root=tmp_path / "photos",
    )

    path = service.ensure_photo_cached("556299999999@s.whatsapp.net")
    profile = storage.get_contact_profile("556299999999@s.whatsapp.net")

    assert Path(path).exists()
    assert Path(path).read_bytes() == b"photo"
    assert profile is not None
    assert profile["profile_picture_path"] == path
