from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    APP_NAME: str = "YkMedia"
    APP_VERSION: str = "0.1.0"

    ENVIRONMENT: str = "development"
    WEBHOOK_SECRET: str = ""

    EVOLUTION_BASE_URL: str = "http://localhost:8080"
    EVOLUTION_API_KEY: str = ""
    EVOLUTION_INSTANCE: str = "ykmedia"
    EVOLUTION_TIMEOUT_SECONDS: float = 10.0

    FILE_STORAGE_ROOT: str = "media"
    CONVERSATION_SESSION_TTL_SECONDS: float = 3600.0
    YOUTUBE_DOWNLOAD_TEMP_ROOT: str = "downloads/youtube"
    FFMPEG_PATH: str = ""
    SQLITE_DATABASE_PATH: str = "data/ykmedia.sqlite3"

    model_config = SettingsConfigDict(
        env_file=".env",
        extra="ignore",
    )


settings = Settings()
