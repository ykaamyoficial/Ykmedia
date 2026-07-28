import base64
from typing import Any

import httpx

from app.core.config import settings
from app.models.download import DownloadedMedia
from app.models.message import ReceivedMessage


class EvolutionClientError(Exception):
    """Base exception for Evolution API integration errors."""


class EvolutionConnectionError(EvolutionClientError):
    """Raised when the Evolution API cannot be reached."""


class EvolutionHttpError(EvolutionClientError):
    def __init__(self, status_code: int, message: str) -> None:
        self.status_code = status_code
        super().__init__(message)


class EvolutionInvalidResponseError(EvolutionClientError):
    """Raised when Evolution returns an invalid or unsupported response."""


class EvolutionClient:
    def __init__(
        self,
        base_url: str | None = None,
        api_key: str | None = None,
        timeout_seconds: float | None = None,
        transport: httpx.AsyncBaseTransport | None = None,
    ) -> None:
        self.base_url = (base_url or settings.EVOLUTION_BASE_URL).rstrip("/")
        self.headers: dict[str, str] = {
            "apikey": api_key if api_key is not None else settings.EVOLUTION_API_KEY
        }
        self.timeout_seconds = (
            timeout_seconds if timeout_seconds is not None else settings.EVOLUTION_TIMEOUT_SECONDS
        )
        self._transport = transport

    async def health(self) -> dict[str, Any]:
        return await self._request_json("GET", "")

    async def send_text_message(self, recipient: str, text: str) -> dict[str, Any]:
        normalized_recipient = self._normalize_recipient(recipient)
        normalized_text = text.strip()
        if not normalized_recipient:
            raise EvolutionInvalidResponseError("Cannot send a text message without a recipient.")
        if not normalized_text:
            raise EvolutionInvalidResponseError("Cannot send an empty text message.")

        return await self._request_json(
            "POST",
            f"/message/sendText/{settings.EVOLUTION_INSTANCE}",
            json={
                "number": normalized_recipient,
                "text": normalized_text,
            },
        )

    async def connect_instance(self) -> dict[str, Any]:
        return await self._request_json(
            "GET",
            f"/instance/connect/{settings.EVOLUTION_INSTANCE}",
        )

    async def get_connection_state(self) -> dict[str, Any]:
        return await self._request_json(
            "GET",
            f"/instance/connectionState/{settings.EVOLUTION_INSTANCE}",
        )

    async def logout_instance(self) -> dict[str, Any]:
        return await self._request_json(
            "DELETE",
            f"/instance/logout/{settings.EVOLUTION_INSTANCE}",
        )

    async def download_media(self, message: ReceivedMessage) -> DownloadedMedia:
        if message.media is None:
            raise EvolutionInvalidResponseError("Cannot download media from a message without media metadata.")

        payload = await self._request_json(
            "POST",
            f"/chat/getBase64FromMediaMessage/{settings.EVOLUTION_INSTANCE}",
            json={
                "message": {
                    "key": {
                        "id": message.message_id,
                        "remoteJid": message.sender.remote_jid,
                        "fromMe": message.sender.is_from_me,
                    }
                },
                "convertToMp4": False,
            },
        )

        base64_content = payload.get("base64")
        if not isinstance(base64_content, str) or not base64_content:
            raise EvolutionInvalidResponseError("Evolution API returned no media base64 content.")

        try:
            content = base64.b64decode(base64_content, validate=True)
        except ValueError as exc:
            raise EvolutionInvalidResponseError("Evolution API returned invalid media base64 content.") from exc

        mimetype = payload.get("mimetype") or payload.get("mediaType") or message.media.mimetype
        if not isinstance(mimetype, str) or not mimetype:
            mimetype = "application/octet-stream"

        file_name = payload.get("fileName") or message.media.file_name

        return DownloadedMedia(
            message_id=message.message_id,
            content=content,
            mimetype=mimetype,
            size_bytes=len(content),
            file_name=str(file_name) if file_name else None,
        )

    async def _request_json(
        self,
        method: str,
        path: str,
        json: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        url = self._build_url(path)

        try:
            async with httpx.AsyncClient(
                timeout=self.timeout_seconds,
                transport=self._transport,
            ) as client:
                response = await client.request(
                    method,
                    url,
                    headers=self.headers,
                    json=json,
                )
                response.raise_for_status()
        except httpx.HTTPStatusError as exc:
            status_code = exc.response.status_code
            raise EvolutionHttpError(
                status_code=status_code,
                message=f"Evolution API returned HTTP {status_code}.",
            ) from exc
        except httpx.RequestError as exc:
            raise EvolutionConnectionError("Could not connect to Evolution API.") from exc

        try:
            payload = response.json()
        except ValueError as exc:
            raise EvolutionInvalidResponseError("Evolution API returned invalid JSON.") from exc

        if not isinstance(payload, dict):
            raise EvolutionInvalidResponseError("Evolution API returned an unsupported JSON payload.")

        return payload

    def _build_url(self, path: str) -> str:
        normalized_path = path.strip("/")
        if not normalized_path:
            return self.base_url

        return f"{self.base_url}/{normalized_path}"

    def _normalize_recipient(self, recipient: str) -> str:
        value = recipient.strip()
        if "@" in value:
            value = value.split("@", 1)[0]

        return "".join(character for character in value if character.isdigit())
