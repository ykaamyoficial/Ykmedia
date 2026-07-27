import asyncio
from pathlib import Path

from app.models.download import DownloadedMedia
from app.models.message import MessageType, ReceivedMessage, Sender
from app.services.youtube_downloader import YoutubeDownloader


class FakeYoutubeDownloader(YoutubeDownloader):
    def __init__(self) -> None:
        super().__init__(temp_root=Path("unused"))
        self.downloaded_url: str | None = None

    def _download_url(self, url: str, message_id: str) -> DownloadedMedia:
        self.downloaded_url = url
        return DownloadedMedia(
            message_id=message_id,
            content=b"video",
            mimetype="video/mp4",
            size_bytes=5,
            file_name="youtube.mp4",
        )


def _message(text: str) -> ReceivedMessage:
    return ReceivedMessage(
        message_id="MSG1",
        sender=Sender(remote_jid="556299999999@s.whatsapp.net"),
        message_type=MessageType.TEXT,
        raw_type="conversation",
        text=text,
    )


def test_detects_valid_youtube_links() -> None:
    downloader = YoutubeDownloader()

    assert downloader.extract_url("Veja https://www.youtube.com/watch?v=abc") == (
        "https://www.youtube.com/watch?v=abc"
    )
    assert downloader.extract_url("https://youtu.be/abc") == "https://youtu.be/abc"
    assert downloader.extract_url("http://youtube.com/watch?v=abc") == "http://youtube.com/watch?v=abc"


def test_rejects_invalid_youtube_link() -> None:
    downloader = YoutubeDownloader()

    assert downloader.extract_url("https://example.com/watch?v=abc") is None
    assert downloader.extract_url("texto comum") is None


def test_simulated_download_returns_downloaded_media() -> None:
    downloader = FakeYoutubeDownloader()

    result = asyncio.run(downloader.download(_message("Baixar https://youtu.be/abc")))

    assert downloader.downloaded_url == "https://youtu.be/abc"
    assert result.message_id == "MSG1"
    assert result.content == b"video"
    assert result.mimetype == "video/mp4"
    assert result.file_name == "youtube.mp4"
