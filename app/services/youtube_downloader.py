import tempfile
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

from app.core.config import settings
from app.models.download import DownloadedMedia
from app.models.message import ReceivedMessage


class YoutubeDownloaderError(Exception):
    """Base exception for YouTube download errors."""


class UnsupportedYoutubeUrlError(YoutubeDownloaderError):
    """Raised when a message does not contain a supported YouTube URL."""


class YoutubeDownloadError(YoutubeDownloaderError):
    """Raised when the YouTube download fails."""


class YoutubeDownloader:
    _SUPPORTED_HOSTS = {
        "youtube.com",
        "www.youtube.com",
        "m.youtube.com",
        "youtu.be",
    }

    def __init__(self, temp_root: str | Path | None = None) -> None:
        self.temp_root = Path(temp_root or settings.YOUTUBE_DOWNLOAD_TEMP_ROOT).resolve()

    def is_supported_url(self, url: str) -> bool:
        parsed_url = urlparse(url.strip())
        return parsed_url.scheme in {"http", "https"} and parsed_url.netloc.lower() in self._SUPPORTED_HOSTS

    def extract_url(self, text: str | None) -> str | None:
        if not text:
            return None

        for token in text.split():
            candidate = token.strip(".,;!?)(")
            if self.is_supported_url(candidate):
                return candidate

        return None

    async def download(self, message: ReceivedMessage) -> DownloadedMedia:
        url = self.extract_url(message.text)
        if url is None:
            raise UnsupportedYoutubeUrlError("Mensagem nao contem link suportado do YouTube.")

        return self._download_url(url=url, message_id=message.message_id)

    def _download_url(self, url: str, message_id: str) -> DownloadedMedia:
        try:
            from yt_dlp import YoutubeDL
        except ImportError as exc:
            raise YoutubeDownloadError("yt-dlp nao esta instalado.") from exc

        self.temp_root.mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryDirectory(dir=self.temp_root) as temp_directory:
            output_template = str(Path(temp_directory) / "%(title).200B.%(ext)s")
            options: dict[str, Any] = {
                "outtmpl": output_template,
                "format": "best[ext=mp4]/best",
                "quiet": True,
                "noplaylist": True,
            }

            try:
                with YoutubeDL(options) as youtube_dl:
                    info = youtube_dl.extract_info(url, download=True)
                    downloaded_path = Path(youtube_dl.prepare_filename(info))
            except Exception as exc:
                raise YoutubeDownloadError("Falha ao baixar video do YouTube.") from exc

            if not downloaded_path.exists():
                raise YoutubeDownloadError("Arquivo baixado do YouTube nao foi encontrado.")

            content = downloaded_path.read_bytes()
            if not content:
                raise YoutubeDownloadError("Arquivo baixado do YouTube esta vazio.")

            mimetype = "video/mp4" if downloaded_path.suffix.lower() == ".mp4" else "application/octet-stream"
            return DownloadedMedia(
                message_id=message_id,
                content=content,
                mimetype=mimetype,
                size_bytes=len(content),
                file_name=downloaded_path.name,
            )
