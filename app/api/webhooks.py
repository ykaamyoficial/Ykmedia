import logging

from fastapi import APIRouter, Depends, Header, HTTPException, Request, status

from app.core.config import settings
from app.services.application_factory import get_receive_media_use_case
from app.services.receive_media_use_case import ReceiveMediaUseCase

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/webhooks", tags=["webhooks"])


@router.post("/evolution")
async def evolution_webhook(
    request: Request,
    x_webhook_secret: str | None = Header(default=None),
    use_case: ReceiveMediaUseCase = Depends(get_receive_media_use_case),
) -> dict[str, object]:
    if settings.WEBHOOK_SECRET and x_webhook_secret != settings.WEBHOOK_SECRET:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Webhook não autorizado.",
        )

    payload = await request.json()
    result = await use_case.execute(payload)

    if result.errors:
        logger.warning("Webhook Evolution processado com erros: %s", result.errors)

    return {
        "received": True,
        "processed": result.received_message is not None,
        "conversation_state": result.conversation_state.value
        if result.conversation_state is not None
        else None,
        "next_message": result.next_message,
        "has_file": result.stored_file is not None,
        "has_errors": bool(result.errors),
    }
