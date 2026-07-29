from fastapi.testclient import TestClient

from app.main import app
from app.models.conversations import (
    ConversationDetails,
    ConversationListResponse,
    ConversationMessageItem,
    ConversationMessagesResponse,
    ConversationProfile,
)
from app.services.application_factory import get_conversation_query_service
from app.services.conversation_query_service import ConversationNotFoundError


class FakeConversationQueryService:
    def list_conversations(self, page: int, page_size: int, search: str) -> ConversationListResponse:
        return ConversationListResponse(
            items=[],
            total=0,
            page=page,
            page_size=page_size,
            has_next=False,
        )

    def get_conversation(self, conversation_id: str) -> ConversationDetails:
        if conversation_id == "missing":
            raise ConversationNotFoundError(conversation_id)
        return ConversationDetails(
            id=conversation_id,
            contact_id="5562999999999@s.whatsapp.net",
            profile=ConversationProfile(
                display_name="Maria",
                phone="(62) 99999-9999",
                profile_photo_url=None,
                profile_photo_path=None,
            ),
            session_status=None,
            category=None,
            created_at="2026-07-29T10:00:00+00:00",
            updated_at="2026-07-29T10:01:00+00:00",
            additional_status=None,
            message_count=1,
            unread_count=0,
            is_active=False,
        )

    def list_messages(self, conversation_id: str, page: int, page_size: int) -> ConversationMessagesResponse:
        if conversation_id == "missing":
            raise ConversationNotFoundError(conversation_id)
        return ConversationMessagesResponse(
            items=[
                ConversationMessageItem(
                    id="msg-1",
                    conversation_id=conversation_id,
                    direction="INBOUND",
                    message_type="text",
                    content="Ola",
                    created_at="2026-07-29T10:00:00+00:00",
                    status="RECEBIDA",
                    sender_name="Maria",
                    media_metadata=None,
                )
            ],
            total=1,
            page=page,
            page_size=page_size,
            has_next=False,
        )


def test_list_conversations_endpoint() -> None:
    app.dependency_overrides[get_conversation_query_service] = lambda: FakeConversationQueryService()
    try:
        response = TestClient(app).get("/conversations?page=2&page_size=10&search=maria")
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    assert response.json()["page"] == 2


def test_get_conversation_endpoint() -> None:
    app.dependency_overrides[get_conversation_query_service] = lambda: FakeConversationQueryService()
    try:
        response = TestClient(app).get("/conversations/abc")
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    assert response.json()["profile"]["display_name"] == "Maria"


def test_get_conversation_endpoint_returns_404() -> None:
    app.dependency_overrides[get_conversation_query_service] = lambda: FakeConversationQueryService()
    try:
        response = TestClient(app).get("/conversations/missing")
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 404


def test_list_conversation_messages_endpoint() -> None:
    app.dependency_overrides[get_conversation_query_service] = lambda: FakeConversationQueryService()
    try:
        response = TestClient(app).get("/conversations/abc/messages?page=1&page_size=25")
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    assert response.json()["items"][0]["content"] == "Ola"
