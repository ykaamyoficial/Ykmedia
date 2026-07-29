import asyncio
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Protocol

import httpx

from app.services.storage_service import StorageService


class ProfilePictureClient(Protocol):
    async def fetch_profile_picture_url(self, number: str) -> dict[str, object]:
        pass


class ContactProfileService:
    def __init__(
        self,
        storage_service: StorageService,
        evolution_client: ProfilePictureClient | None = None,
        cache_root: str | Path = "data/contact_photos",
        ttl_hours: int = 24,
    ) -> None:
        self._storage_service = storage_service
        self._evolution_client = evolution_client
        self._cache_root = Path(cache_root).resolve()
        self._ttl = timedelta(hours=ttl_hours)

    def get_cached_photo_path(self, sender: str) -> str:
        profile = self._storage_service.get_contact_profile(sender)
        if not profile:
            return ""
        path = str(profile.get("profile_picture_path") or "")
        if path and Path(path).exists():
            return path
        return ""

    def ensure_photo_cached(self, sender: str) -> str:
        cached = self.get_cached_photo_path(sender)
        if cached and not self._is_expired(sender):
            return cached
        if self._evolution_client is None:
            return cached

        try:
            payload = asyncio.run(self._evolution_client.fetch_profile_picture_url(sender))
        except Exception:
            return cached

        url = self._extract_url(payload)
        if not url:
            return cached

        try:
            photo_path = self._download_photo(sender, url)
        except httpx.HTTPError:
            return cached

        self._storage_service.save_contact_profile(
            sender=sender,
            profile_picture_url=url,
            profile_picture_path=str(photo_path),
            updated_at=datetime.now(timezone.utc).isoformat(timespec="seconds"),
        )
        return str(photo_path)

    def _is_expired(self, sender: str) -> bool:
        profile = self._storage_service.get_contact_profile(sender)
        if not profile:
            return True
        updated_at = str(profile.get("updated_at") or "")
        try:
            parsed = datetime.fromisoformat(updated_at.replace("Z", "+00:00"))
        except ValueError:
            return True
        return datetime.now(timezone.utc) - parsed >= self._ttl

    def _extract_url(self, payload: dict[str, object]) -> str:
        for key in ("profilePictureUrl", "profilePicUrl", "pictureUrl"):
            value = payload.get(key)
            if isinstance(value, str) and value.strip():
                return value.strip()
        return ""

    def _download_photo(self, sender: str, url: str) -> Path:
        self._cache_root.mkdir(parents=True, exist_ok=True)
        target = self._cache_root / f"{self._safe_sender(sender)}.jpg"
        response = httpx.get(url, timeout=10.0)
        response.raise_for_status()
        target.write_bytes(response.content)
        return target

    def _safe_sender(self, sender: str) -> str:
        return "".join(character for character in sender if character.isalnum())
