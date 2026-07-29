from fastapi import APIRouter, Depends, HTTPException, Query

from app.models.conversations import (
    ConversationDetails,
    ConversationListResponse,
    ConversationMessagesResponse,
)
from app.services.application_factory import get_conversation_query_service
from app.services.conversation_query_service import ConversationNotFoundError, ConversationQueryService

router = APIRouter(prefix="/conversations", tags=["conversations"])


@router.get("", response_model=ConversationListResponse)
def list_conversations(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=30, ge=1, le=100),
    search: str = Query(default="", max_length=120),
    service: ConversationQueryService = Depends(get_conversation_query_service),
) -> ConversationListResponse:
    return service.list_conversations(page=page, page_size=page_size, search=search)


@router.get("/{conversation_id}", response_model=ConversationDetails)
def get_conversation(
    conversation_id: str,
    service: ConversationQueryService = Depends(get_conversation_query_service),
) -> ConversationDetails:
    try:
        return service.get_conversation(conversation_id)
    except ConversationNotFoundError:
        raise HTTPException(status_code=404, detail="Conversation not found.") from None


@router.get("/{conversation_id}/messages", response_model=ConversationMessagesResponse)
def list_conversation_messages(
    conversation_id: str,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=50, ge=1, le=100),
    service: ConversationQueryService = Depends(get_conversation_query_service),
) -> ConversationMessagesResponse:
    try:
        return service.list_messages(
            conversation_id=conversation_id,
            page=page,
            page_size=page_size,
        )
    except ConversationNotFoundError:
        raise HTTPException(status_code=404, detail="Conversation not found.") from None
