from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class DownloadedMedia:
    message_id: str
    content: bytes
    mimetype: str
    size_bytes: int
    file_name: str | None = None
