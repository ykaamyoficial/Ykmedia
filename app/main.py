from fastapi import FastAPI

from app.api.webhooks import router as webhooks_router
from app.core.config import settings
from app.services.application_factory import get_evolution_client


def create_app() -> FastAPI:
    application = FastAPI(
        title=settings.APP_NAME,
        version=settings.APP_VERSION,
    )

    application.include_router(webhooks_router)

    @application.get("/")
    async def home() -> dict[str, str]:
        return {"project": settings.APP_NAME}

    @application.get("/health")
    async def health() -> dict[str, str]:
        return {"status": "ok"}

    @application.get("/evolution")
    async def evolution_status() -> dict[str, object]:
        return await get_evolution_client().health()

    return application


app = create_app()
