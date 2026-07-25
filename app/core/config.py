from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    APP_NAME: str = "YkMedia"
    APP_VERSION: str = "0.1.0"

    ENVIRONMENT: str = "development"
    WEBHOOK_SECRET: str = ""

    EVOLUTION_BASE_URL: str = "http://localhost:8080"
    EVOLUTION_API_KEY: str = ""
    EVOLUTION_INSTANCE: str = "ykmedia"

    model_config = SettingsConfigDict(
        env_file=".env",
        extra="ignore",
    )


settings = Settings()