import logging
from fastapi import APIRouter, Header, HTTPException, Request, status

from app.core.config import settings
from app.services.message_processor import process_evolution_event

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/webhooks", tags=["webhooks"])


@router.post("/evolution")
async def evolution_webhook(
    request: Request,
    x_webhook_secret: str | None = Header(default=None),
) -> dict[str, object]:
    if settings.webhook_secret and x_webhook_secret != settings.webhook_secret:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Webhook não autorizado.",
        )

    payload = await request.json()
    result = await process_evolution_event(payload)
    return {"received": True, **result}
