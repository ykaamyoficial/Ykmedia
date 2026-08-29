"""Executable entry point for the packaged YkMedia FastAPI backend."""

import os
import secrets
from pathlib import Path


def _load_docker_api_key(runtime_root: Path) -> str | None:
    """Reuse the key of an existing Docker environment before loading settings."""
    environment_file = runtime_root / "docker" / ".env"
    if not environment_file.is_file():
        return None

    for line in environment_file.read_text(encoding="utf-8").splitlines():
        key, separator, value = line.partition("=")
        if separator and key.strip() == "EVOLUTION_API_KEY" and value.strip():
            return value.strip()
    return None


def prepare_runtime_environment() -> Path:
    """Configure a per-user runtime directory before importing application settings."""
    runtime_root = Path(
        os.environ.get(
            "YKMEDIA_RUNTIME_ROOT",
            Path(os.environ.get("LOCALAPPDATA", Path.home() / "AppData" / "Local")) / "YkMedia",
        )
    ).resolve()

    runtime_root.mkdir(parents=True, exist_ok=True)
    defaults = {
        "ENVIRONMENT": "production",
        "FILE_STORAGE_ROOT": str(runtime_root / "media"),
        "YOUTUBE_DOWNLOAD_TEMP_ROOT": str(runtime_root / "downloads" / "youtube"),
        "SQLITE_DATABASE_PATH": str(runtime_root / "data" / "ykmedia.sqlite3"),
    }
    for key, value in defaults.items():
        os.environ.setdefault(key, value)

    _ensure_api_auth_token(runtime_root)

    os.chdir(runtime_root)
    docker_api_key = _load_docker_api_key(runtime_root)
    if docker_api_key:
        # Existing containers keep their key after an application update. Docker is
        # authoritative here, otherwise the backend could start with a stale key.
        os.environ["EVOLUTION_API_KEY"] = docker_api_key
    return runtime_root


def _ensure_api_auth_token(runtime_root: Path) -> str:
    """Persist a stable API token so the Tauri UI and the backend agree on it.

    The token lives next to the SQLite database. The Tauri shell reads the same
    file and forwards the value to the web UI, which sends it on every request.
    """
    if os.environ.get("API_AUTH_TOKEN"):
        return os.environ["API_AUTH_TOKEN"]

    token_file = runtime_root / "data" / "api_token"
    token_file.parent.mkdir(parents=True, exist_ok=True)

    token = ""
    if token_file.is_file():
        token = token_file.read_text(encoding="utf-8").strip()

    if not token:
        token = secrets.token_urlsafe(32)
        token_file.write_text(token, encoding="utf-8")

    os.environ["API_AUTH_TOKEN"] = token
    return token


def main() -> None:
    prepare_runtime_environment()

    import uvicorn

    from app.core.config import settings
    from app.main import app

    uvicorn.run(
        app,
        host=settings.BACKEND_HOST,
        port=settings.BACKEND_PORT,
        log_level="info",
    )


if __name__ == "__main__":
    main()
