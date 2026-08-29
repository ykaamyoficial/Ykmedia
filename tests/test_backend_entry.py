import os
from pathlib import Path

from app.backend_entry import prepare_runtime_environment


def test_prepare_runtime_environment_uses_per_user_directories(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setenv("YKMEDIA_RUNTIME_ROOT", str(tmp_path))
    monkeypatch.delenv("FILE_STORAGE_ROOT", raising=False)
    monkeypatch.delenv("YOUTUBE_DOWNLOAD_TEMP_ROOT", raising=False)
    monkeypatch.delenv("SQLITE_DATABASE_PATH", raising=False)
    monkeypatch.delenv("ENVIRONMENT", raising=False)
    monkeypatch.chdir(tmp_path.parent)

    runtime_root = prepare_runtime_environment()

    assert runtime_root == tmp_path.resolve()
    assert Path.cwd() == tmp_path.resolve()
    assert Path(os.environ["FILE_STORAGE_ROOT"]) == tmp_path / "media"
    assert Path(os.environ["YOUTUBE_DOWNLOAD_TEMP_ROOT"]) == tmp_path / "downloads" / "youtube"
    assert Path(os.environ["SQLITE_DATABASE_PATH"]) == tmp_path / "data" / "ykmedia.sqlite3"


def test_prepare_runtime_environment_generates_and_persists_api_token(
    tmp_path: Path, monkeypatch
) -> None:
    monkeypatch.setenv("YKMEDIA_RUNTIME_ROOT", str(tmp_path))
    monkeypatch.delenv("API_AUTH_TOKEN", raising=False)

    prepare_runtime_environment()

    token = os.environ["API_AUTH_TOKEN"]
    token_file = tmp_path / "data" / "api_token"
    assert token
    assert token_file.read_text(encoding="utf-8").strip() == token

    monkeypatch.delenv("API_AUTH_TOKEN", raising=False)
    prepare_runtime_environment()
    assert os.environ["API_AUTH_TOKEN"] == token


def test_prepare_runtime_environment_reuses_existing_docker_api_key(tmp_path: Path, monkeypatch) -> None:
    (tmp_path / "docker").mkdir()
    (tmp_path / "docker" / ".env").write_text("EVOLUTION_API_KEY=container-key\n", encoding="utf-8")
    monkeypatch.setenv("YKMEDIA_RUNTIME_ROOT", str(tmp_path))
    monkeypatch.delenv("EVOLUTION_API_KEY", raising=False)

    prepare_runtime_environment()

    assert os.environ["EVOLUTION_API_KEY"] == "container-key"
