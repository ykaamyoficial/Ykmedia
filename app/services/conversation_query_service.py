import base64
import re
from pathlib import Path
from typing import Any

from app.core.config import settings
from app.models.conversations import (
    ConversationDetails,
    ConversationListItem,
    ConversationListResponse,
    ConversationMessageItem,
    ConversationMessagesResponse,
    ConversationProfile,
)
from app.services.storage_service import StorageService


class ConversationNotFoundError(Exception):
    pass


class ConversationQueryService:
    def __init__(self, storage_service: StorageService) -> None:
        self._storage_service = storage_service

    def list_conversations(
        self,
        page: int = 1,
        page_size: int = 30,
        search: str = "",
    ) -> ConversationListResponse:
        safe_page = max(page, 1)
        safe_page_size = max(1, min(page_size, 100))
        offset = (safe_page - 1) * safe_page_size
        total = self._storage_service.count_conversation_contacts(search)
        rows = self._storage_service.list_conversation_contacts_paginated(
            search_text=search,
            limit=safe_page_size,
            offset=offset,
        )

        return ConversationListResponse(
            items=[self._row_to_list_item(row) for row in rows],
            total=total,
            page=safe_page,
            page_size=safe_page_size,
            has_next=offset + safe_page_size < total,
        )

    def get_conversation(self, conversation_id: str) -> ConversationDetails:
        sender = self._decode_conversation_id(conversation_id)
        row = self._storage_service.get_conversation_contact(sender)
        if row is None:
            raise ConversationNotFoundError(conversation_id)

        profile = self._build_profile(row)
        return ConversationDetails(
            id=self._encode_conversation_id(sender),
            contact_id=sender,
            profile=profile,
            session_status=self._optional_string(row.get("session_state")),
            category=self._optional_string(row.get("category")),
            created_at=self._optional_string(row.get("first_activity")),
            updated_at=self._optional_string(row.get("last_activity")),
            additional_status=self._optional_string(row.get("last_status")),
            message_count=int(row.get("media_count") or row.get("message_count") or 0),
            unread_count=0,
            is_active=self._is_active(row),
        )

    def list_messages(
        self,
        conversation_id: str,
        page: int = 1,
        page_size: int = 50,
    ) -> ConversationMessagesResponse:
        sender = self._decode_conversation_id(conversation_id)
        if self._storage_service.get_conversation_contact(sender) is None:
            raise ConversationNotFoundError(conversation_id)

        safe_page = max(page, 1)
        safe_page_size = max(1, min(page_size, 100))
        offset = (safe_page - 1) * safe_page_size
        total = self._storage_service.count_conversation_messages(sender)
        rows = self._storage_service.list_conversation_messages_paginated(
            sender=sender,
            limit=safe_page_size,
            offset=offset,
        )
        media_rows = self._storage_service.list_media_by_sender(sender)
        profile = self._build_profile({"sender": sender})
        items = [
            self._row_to_message(row, conversation_id, profile.display_name)
            for row in rows
        ]
        items.extend(
            self._media_history_to_message(row, conversation_id, profile.display_name)
            for row in media_rows
        )
        items.sort(key=lambda item: item.created_at)

        return ConversationMessagesResponse(
            items=items,
            total=total,
            page=safe_page,
            page_size=safe_page_size,
            has_next=offset + safe_page_size < total,
        )

    def _row_to_list_item(self, row: dict[str, Any]) -> ConversationListItem:
        sender = str(row["sender"])
        profile = self._build_profile(row)
        return ConversationListItem(
            id=self._encode_conversation_id(sender),
            contact_id=sender,
            display_name=profile.display_name,
            phone=profile.phone,
            profile_photo_url=profile.profile_photo_url,
            last_message_preview=self._preview(row.get("last_media_content") or row.get("last_content")),
            last_message_at=self._optional_string(row.get("last_media_activity") or row.get("last_activity")),
            last_message_direction=self._optional_string(row.get("last_direction")),
            unread_count=0,
            session_status=self._optional_string(row.get("session_state") or row.get("last_state")),
            category=self._optional_string(row.get("category")),
            is_active=self._is_active(row),
            message_count=int(row.get("media_count") or row.get("message_count") or 0),
        )

    def _row_to_message(
        self,
        row: dict[str, Any],
        conversation_id: str,
        sender_name: str,
    ) -> ConversationMessageItem:
        return ConversationMessageItem(
            id=str(row["id"]),
            conversation_id=conversation_id,
            direction=str(row["direction"]),
            message_type=str(row["message_type"]),
            content=str(row["content"]),
            created_at=str(row["created_at"]),
            status=str(row["status"]),
            sender_name=sender_name,
            media_metadata={"media_id": str(row["media_id"])} if row.get("media_id") else None,
        )

    def _media_history_to_message(
        self,
        row: dict[str, Any],
        conversation_id: str,
        sender_name: str,
    ) -> ConversationMessageItem:
        final_name = self._optional_string(row.get("final_name"))
        file_path = self._optional_string(row.get("file_path"))
        absolute_path = self._resolve_media_path(file_path) if file_path else None
        metadata: dict[str, object] = {
            "history_id": str(row.get("id") or ""),
            "final_name": final_name or file_path or "Arquivo",
            "file_path": file_path or "",
            "absolute_path": str(absolute_path) if absolute_path is not None else "",
            "category": self._optional_string(row.get("category")) or "",
            "origin": self._optional_string(row.get("origin")) or "",
        }
        if absolute_path is not None and absolute_path.exists():
            metadata["size"] = absolute_path.stat().st_size
            metadata["exists"] = True
        else:
            metadata["exists"] = False

        return ConversationMessageItem(
            id=f"media-history-{row.get('id')}",
            conversation_id=conversation_id,
            direction="EVENT",
            message_type=self._media_kind_from_name(final_name or file_path or "", row.get("origin")),
            content=final_name or file_path or "Arquivo salvo",
            created_at=str(row.get("date") or ""),
            status=str(row.get("status") or ""),
            sender_name=sender_name,
            media_metadata=metadata,
        )

    def _resolve_media_path(self, file_path: str) -> Path:
        path = Path(file_path)
        if path.is_absolute():
            return path
        return Path(settings.FILE_STORAGE_ROOT).resolve() / path

    def _media_kind_from_name(self, file_name: str, origin: object) -> str:
        if self._optional_string(origin or "") == "YouTube":
            return "youtube"
        suffix = Path(file_name).suffix.lower()
        if suffix in {".jpg", ".jpeg", ".png", ".webp", ".gif"}:
            return "imagem"
        if suffix in {".mp3", ".ogg", ".wav", ".m4a", ".aac", ".opus"}:
            return "audio"
        if suffix in {".mp4", ".mov", ".mkv", ".webm", ".avi"}:
            return "video"
        if suffix in {".pdf", ".doc", ".docx", ".xls", ".xlsx", ".ppt", ".pptx", ".txt"}:
            return "documento"
        return "arquivo"

    def _build_profile(self, row: dict[str, Any]) -> ConversationProfile:
        sender = str(row["sender"])
        phone = self._format_phone(sender)
        display_name = self._resolve_display_name(
            self._optional_string(row.get("display_name")),
            phone,
        )
        return ConversationProfile(
            display_name=display_name,
            phone=phone,
            profile_photo_url=self._optional_string(row.get("profile_picture_url")),
            profile_photo_path=self._optional_string(row.get("profile_picture_path")),
        )

    def _resolve_display_name(self, saved_name: str | None, fallback_phone: str) -> str:
        if saved_name:
            return saved_name
        return fallback_phone

    def _format_phone(self, sender: str) -> str:
        number = sender.split("@", 1)[0]
        digits = re.sub(r"\D", "", number)
        if not digits:
            return sender

        if digits.startswith("55") and len(digits) in (12, 13):
            area_code = digits[2:4]
            local = digits[4:]
            if len(local) == 9:
                return f"({area_code}) {local[:5]}-{local[5:]}"
            if len(local) == 8:
                return f"({area_code}) {local[:4]}-{local[4:]}"

        if sender.endswith("@s.whatsapp.net") or sender.endswith("@c.us"):
            return f"+{digits}"
        return sender

    def _encode_conversation_id(self, sender: str) -> str:
        return base64.urlsafe_b64encode(sender.encode("utf-8")).decode("ascii").rstrip("=")

    def _decode_conversation_id(self, conversation_id: str) -> str:
        padding = "=" * (-len(conversation_id) % 4)
        try:
            return base64.urlsafe_b64decode(f"{conversation_id}{padding}").decode("utf-8")
        except (ValueError, UnicodeDecodeError):
            raise ConversationNotFoundError(conversation_id) from None

    def _is_active(self, row: dict[str, Any]) -> bool:
        state = self._optional_string(row.get("session_state"))
        return bool(state and state != "FINISHED")

    def _preview(self, value: object) -> str | None:
        text = self._optional_string(value)
        if not text:
            return None
        return text if len(text) <= 90 else f"{text[:87]}..."

    def _optional_string(self, value: object) -> str | None:
        if value is None:
            return None
        text = str(value).strip()
        return text or None
