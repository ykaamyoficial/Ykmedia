from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    APP_NAME: str = "YkMedia"
    APP_VERSION: str = "0.3.2"

    ENVIRONMENT: str = "development"
    WEBHOOK_SECRET: str = ""

    # Token exigido nas rotas de API voltadas ao aplicativo. Quando vazio (modo
    # desenvolvimento) a verificacao e desativada; o executavel empacotado gera e
    # persiste um valor automaticamente. Ver app/backend_entry.py.
    API_AUTH_TOKEN: str = ""

    EVOLUTION_BASE_URL: str = "http://localhost:8080"
    EVOLUTION_API_KEY: str = ""
    EVOLUTION_INSTANCE: str = "ykmedia"
    EVOLUTION_TIMEOUT_SECONDS: float = 10.0

    FILE_STORAGE_ROOT: str = "media"
    CONVERSATION_SESSION_TTL_SECONDS: float = 3600.0
    # Tempo sem resposta ate a conversa expirar (o cliente e avisado antes).
    CONVERSATION_FLOW_TIMEOUT_SECONDS: float = 1800.0
    # Manda o aviso "sua conversa expira em breve" quando faltar este tanto.
    SESSION_EXPIRY_WARNING_SECONDS: float = 300.0
    SESSION_EXPIRY_NOTIFIER_ENABLED: bool = True
    # Janela para agrupar varios arquivos enviados em sequencia num unico lote.
    MEDIA_GROUPING_WINDOW_SECONDS: float = 8.0
    YOUTUBE_DOWNLOAD_TEMP_ROOT: str = "downloads/youtube"
    # Altura maxima do video baixado do YouTube. Sem limite o yt-dlp escolhe 4K
    # (mais de 1 GB por video), o que nao faz sentido para projecao no culto.
    YOUTUBE_MAX_HEIGHT: int = 1080
    FFMPEG_PATH: str = ""
    SQLITE_DATABASE_PATH: str = "data/ykmedia.sqlite3"

    # Worker de fundo que reprocessa jobs que falharam por causas transitorias.
    QUEUE_RETRY_WORKER_ENABLED: bool = True

    BACKEND_HOST: str = "0.0.0.0"
    BACKEND_PORT: int = 8010
    BACKEND_HEALTH_URL: str = "http://localhost:8010/health"
    BACKEND_MONITOR_INTERVAL_SECONDS: float = 5.0
    BACKEND_STARTUP_TIMEOUT_SECONDS: float = 20.0
    BACKEND_RESTART_ATTEMPTS: int = 3
    FRONTEND_CORS_ORIGINS: str = (
        "http://127.0.0.1:5173,"
        "http://localhost:5173,"
        "tauri://localhost,"
        "http://tauri.localhost,"
        "https://tauri.localhost"
    )

    model_config = SettingsConfigDict(
        env_file=".env",
        extra="ignore",
    )


settings = Settings()
