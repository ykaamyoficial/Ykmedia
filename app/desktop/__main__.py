import sys

import uvicorn

from app.core.config import settings


if __name__ == "__main__":
    if "--backend" in sys.argv:
        uvicorn.run(
            "app.main:app",
            host=settings.BACKEND_HOST,
            port=settings.BACKEND_PORT,
            log_level="info",
        )
        raise SystemExit(0)

    from app.desktop.main_window import run

    raise SystemExit(run())
