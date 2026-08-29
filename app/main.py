from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.categories import router as categories_router
from app.api.conversations import router as conversations_router
from app.api.dashboard import router as dashboard_router
from app.api.downloads import router as downloads_router
from app.api.files import router as files_router
from app.api.history import router as history_router
from app.api.settings import router as settings_router
from app.api.security import require_api_token
from app.api.webhooks import router as webhooks_router
from app.core.config import settings
from app.services.application_factory import get_evolution_client

_TAURI_CORS_ORIGINS = ("tauri://localhost", "http://tauri.localhost", "https://tauri.localhost")


def _cors_origins() -> list[str]:
    configured_origins = [
        origin.strip()
        for origin in settings.FRONTEND_CORS_ORIGINS.split(",")
        if origin.strip()
    ]
    return list(dict.fromkeys([*configured_origins, *_TAURI_CORS_ORIGINS]))


@asynccontextmanager
async def _lifespan(_: FastAPI) -> AsyncIterator[None]:
    worker = None
    if settings.QUEUE_RETRY_WORKER_ENABLED:
        from app.services.application_factory import get_queue_retry_worker

        worker = get_queue_retry_worker()
        worker.start()
    try:
        yield
    finally:
        if worker is not None:
            await worker.stop()


def create_app() -> FastAPI:
    application = FastAPI(
        title=settings.APP_NAME,
        version=settings.APP_VERSION,
        lifespan=_lifespan,
    )

    application.add_middleware(
        CORSMiddleware,
        allow_origins=_cors_origins(),
        allow_credentials=False,
        allow_methods=["GET", "POST", "PUT", "DELETE"],
        allow_headers=["Accept", "Content-Type"],
    )

    protected = [Depends(require_api_token)]

    application.include_router(webhooks_router)
    application.include_router(dashboard_router, dependencies=protected)
    application.include_router(conversations_router, dependencies=protected)
    application.include_router(downloads_router, dependencies=protected)
    application.include_router(files_router, dependencies=protected)
    application.include_router(history_router, dependencies=protected)
    application.include_router(categories_router, dependencies=protected)
    application.include_router(settings_router, dependencies=protected)

    @application.get("/")
    async def home() -> dict[str, str]:
        return {"project": settings.APP_NAME}

    @application.get("/health")
    async def health() -> dict[str, str]:
        return {"status": "ok"}

    @application.get("/evolution", dependencies=protected)
    async def evolution_status() -> dict[str, object]:
        return await get_evolution_client().health()

    return application


app = create_app()
