import asyncio

import pytest

from app.models.download import DownloadedMedia
from app.models.message import Media, MessageType, ReceivedMessage, Sender
from app.services.download_manager import DownloadManager, MessageWithoutMediaError
from app.services.evolution_client import (
    EvolutionConnectionError,
    EvolutionHttpError,
    EvolutionInvalidResponseError,
)


class FakeEvolutionClient:
    def __init__(self, result: DownloadedMedia | Exception) -> None:
        self.result = result
        self.received_message: ReceivedMessage | None = None

    async def download_media(self, message: ReceivedMessage) -> DownloadedMedia:
        self.received_message = message

        if isinstance(self.result, Exception):
            raise self.result

        return self.result


def _media_message() -> ReceivedMessage:
    return ReceivedMessage(
        message_id="MSG1",
        sender=Sender(remote_jid="556299999999@s.whatsapp.net"),
        message_type=MessageType.AUDIO,
        raw_type="audioMessage",
        media=Media(mimetype="audio/ogg", file_name="audio.ogg"),
    )


def test_downloads_valid_media() -> None:
    message = _media_message()
    downloaded_media = DownloadedMedia(
        message_id="MSG1",
        content=b"audio",
        mimetype="audio/ogg",
        size_bytes=5,
        file_name="audio.ogg",
    )
    evolution_client = FakeEvolutionClient(downloaded_media)
    manager = DownloadManager(evolution_client)

    result = asyncio.run(manager.download(message))

    assert result == downloaded_media
    assert evolution_client.received_message == message


def test_rejects_message_without_media() -> None:
    message = ReceivedMessage(
        message_id="MSG1",
        sender=Sender(remote_jid="556299999999@s.whatsapp.net"),
        message_type=MessageType.TEXT,
        raw_type="conversation",
        text="Ola",
    )
    manager = DownloadManager(FakeEvolutionClient(Exception("unused")))

    with pytest.raises(MessageWithoutMediaError):
        asyncio.run(manager.download(message))


def test_propagates_connection_error() -> None:
    manager = DownloadManager(FakeEvolutionClient(EvolutionConnectionError("connection failed")))

    with pytest.raises(EvolutionConnectionError):
        asyncio.run(manager.download(_media_message()))


def test_propagates_http_error() -> None:
    manager = DownloadManager(FakeEvolutionClient(EvolutionHttpError(500, "http error")))

    with pytest.raises(EvolutionHttpError):
        asyncio.run(manager.download(_media_message()))


def test_propagates_invalid_response_error() -> None:
    manager = DownloadManager(
        FakeEvolutionClient(EvolutionInvalidResponseError("invalid response"))
    )

    with pytest.raises(EvolutionInvalidResponseError):
        asyncio.run(manager.download(_media_message()))
