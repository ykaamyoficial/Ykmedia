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
    _VIDEO_WITH_AUDIO_FORMAT = (
        "best[ext=mp4][vcodec!=none][acodec!=none]/"
        "best[vcodec!=none][acodec!=none]/"
        "bestvideo[ext=mp4]+bestaudio[ext=m4a]/"
        "bestvideo+bestaudio"
    )
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
            temp_path = Path(temp_directory)
            output_template = str(temp_path / "%(title).200B.%(ext)s")
            options = self._build_download_options(output_template)

            try:
                with YoutubeDL(options) as youtube_dl:
                    info = youtube_dl.extract_info(url, download=True)
                    downloaded_path = self._resolve_downloaded_path(
                        info=info,
                        prepared_path=Path(youtube_dl.prepare_filename(info)),
                        temp_directory=temp_path,
                    )
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

    def _build_download_options(self, output_template: str) -> dict[str, Any]:
        options: dict[str, Any] = {
            "outtmpl": output_template,
            "format": self._VIDEO_WITH_AUDIO_FORMAT,
            "merge_output_format": "mp4",
            "quiet": True,
            "noplaylist": True,
        }

        if settings.FFMPEG_PATH:
            options["ffmpeg_location"] = settings.FFMPEG_PATH

        return options

    def _resolve_downloaded_path(
        self,
        info: dict[str, Any],
        prepared_path: Path,
        temp_directory: Path,
    ) -> Path:
        candidates = [prepared_path, prepared_path.with_suffix(".mp4")]

        requested_downloads = info.get("requested_downloads")
        if isinstance(requested_downloads, list):
            for download in requested_downloads:
                if not isinstance(download, dict):
                    continue

                filepath = download.get("filepath") or download.get("_filename")
                if isinstance(filepath, str):
                    candidates.append(Path(filepath))

        for candidate in candidates:
            if candidate.exists() and candidate.is_file():
                return candidate

        downloaded_files = sorted(
            (path for path in temp_directory.iterdir() if path.is_file()),
            key=lambda path: path.stat().st_mtime,
            reverse=True,
        )
        if downloaded_files:
            return downloaded_files[0]

        return prepared_path
