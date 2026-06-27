from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "EasyOrder"
    app_env: str = "local"
    backend_cors_origins: str = "http://localhost:5173"
    database_url: str = "postgresql://easyorder:easyorder@localhost:5432/easyorder"
    whatsapp_provider_mode: str = "mock"
    swiggy_client_mode: str = "mock"
    llm_mode: str = "mock"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    @property
    def cors_origins(self) -> list[str]:
        return [origin.strip() for origin in self.backend_cors_origins.split(",") if origin.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
