from datetime import datetime
from typing import Any

from app.models.downloads import ClearCompletedDownloadsResponse, DownloadJobItem, DownloadJobsResponse
from app.services.processing_queue import ProcessingQueue


class DownloadQueryService:
    def __init__(self, processing_queue: ProcessingQueue) -> None:
        self._processing_queue = processing_queue

    def list_jobs(self) -> DownloadJobsResponse:
        items = [
            DownloadJobItem(
                id=job.id,
                short_id=job.id[:8],
                sender=self._format_phone(job.sender),
                sender_raw=job.sender,
                origin=job.origin.value,
                file=self._extract_payload_file_label(job.payload),
                kind=self._extract_payload_kind_label(job.payload),
                status=job.status.value,
                created_at=self._format_datetime(job.created_at.isoformat(timespec="seconds")),
            )
            for job in self._processing_queue.list_jobs()
        ]
        return DownloadJobsResponse(items=items, total=len(items))

    def clear_completed(self) -> ClearCompletedDownloadsResponse:
        return ClearCompletedDownloadsResponse(removed=self._processing_queue.clear_completed())

    def _format_phone(self, value: str) -> str:
        number = value.split("@", 1)[0]
        digits = "".join(character for character in number if character.isdigit())
        if len(digits) == 13 and digits.startswith("55"):
            return f"+55 {digits[2:4]} {digits[4:9]}-{digits[9:]}"
        if len(digits) == 12 and digits.startswith("55"):
            return f"+55 {digits[2:4]} {digits[4:8]}-{digits[8:]}"
        if digits:
            return f"+{digits}" if digits.startswith("55") else digits
        return value or "-"

    def _format_datetime(self, value: str) -> str:
        if not value:
            return "-"

        try:
            parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
        except ValueError:
            return value

        return parsed.strftime("%d/%m/%Y %H:%M")

    def _extract_payload_file_label(self, payload: dict[str, Any]) -> str:
        data = payload.get("data")
        if not isinstance(data, dict):
            return "-"
        message = data.get("message")
        if not isinstance(message, dict):
            return "-"
        for value in message.values():
            if isinstance(value, dict):
                file_name = value.get("fileName") or value.get("caption") or value.get("mimetype")
                if file_name:
                    return str(file_name)
            if isinstance(value, str) and "youtu" in value:
                return value
        return str(data.get("messageType") or "-")

    def _extract_payload_kind_label(self, payload: dict[str, Any]) -> str:
        data = payload.get("data")
        if not isinstance(data, dict):
            return "Arquivo"
        raw_type = str(data.get("messageType") or "")
        labels = {
            "imageMessage": "Imagem",
            "audioMessage": "Audio",
            "videoMessage": "Video",
            "documentMessage": "Documento",
            "conversation": "Texto",
        }
        return labels.get(raw_type, "Arquivo")
