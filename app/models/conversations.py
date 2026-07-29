from pydantic import BaseModel


class PaginationMetadata(BaseModel):
    total: int
    page: int
    page_size: int
    has_next: bool


class ConversationProfile(BaseModel):
    display_name: str
    phone: str
    profile_photo_url: str | None = None
    profile_photo_path: str | None = None


class ConversationListItem(BaseModel):
    id: str
    contact_id: str
    display_name: str
    phone: str
    profile_photo_url: str | None = None
    last_message_preview: str | None = None
    last_message_at: str | None = None
    last_message_direction: str | None = None
    unread_count: int
    session_status: str | None = None
    category: str | None = None
    is_active: bool
    message_count: int


class ConversationListResponse(PaginationMetadata):
    items: list[ConversationListItem]


class ConversationDetails(BaseModel):
    id: str
    contact_id: str
    profile: ConversationProfile
    session_status: str | None = None
    category: str | None = None
    created_at: str | None = None
    updated_at: str | None = None
    additional_status: str | None = None
    message_count: int
    unread_count: int
    is_active: bool


class ConversationMessageItem(BaseModel):
    id: str
    conversation_id: str
    direction: str
    message_type: str
    content: str
    created_at: str
    status: str
    sender_name: str
    media_metadata: dict[str, object] | None = None


class ConversationMessagesResponse(PaginationMetadata):
    items: list[ConversationMessageItem]
