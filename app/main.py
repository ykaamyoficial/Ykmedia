from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.categories import router as categories_router
from app.api.conversations import router as conversations_router
from app.api.dashboard import router as dashboard_router
from app.api.downloads import router as downloads_router
from app.api.files import router as files_router
from app.api.history import router as history_router
from app.api.settings import router as settings_router
from app.api.webhooks import router as webhooks_router
from app.core.config import settings
from app.services.application_factory import get_evolution_client


def _cors_origins() -> list[str]:
    return [
        origin.strip()
        for origin in settings.FRONTEND_CORS_ORIGINS.split(",")
        if origin.strip()
    ]


def create_app() -> FastAPI:
    application = FastAPI(
        title=settings.APP_NAME,
        version=settings.APP_VERSION,
    )

    application.add_middleware(
        CORSMiddleware,
        allow_origins=_cors_origins(),
        allow_credentials=False,
        allow_methods=["GET", "POST", "PUT", "DELETE"],
        allow_headers=["Accept", "Content-Type"],
    )

    application.include_router(webhooks_router)
    application.include_router(dashboard_router)
    application.include_router(conversations_router)
    application.include_router(downloads_router)
    application.include_router(files_router)
    application.include_router(history_router)
    application.include_router(categories_router)
    application.include_router(settings_router)

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
