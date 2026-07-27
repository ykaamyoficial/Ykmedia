from typing import Protocol

from app.models.download import DownloadedMedia
from app.models.message import ReceivedMessage


class MediaDownloader(Protocol):
    async def download_media(self, message: ReceivedMessage) -> DownloadedMedia:
        pass


class DownloadManagerError(Exception):
    """Base exception for media download orchestration errors."""


class MessageWithoutMediaError(DownloadManagerError):
    """Raised when a message has no media to download."""


class DownloadManager:
    def __init__(self, evolution_client: MediaDownloader) -> None:
        self._evolution_client = evolution_client

    async def download(self, message: ReceivedMessage) -> DownloadedMedia:
        if message.media is None:
            raise MessageWithoutMediaError("Mensagem recebida nao possui midia.")

        return await self._evolution_client.download_media(message)
