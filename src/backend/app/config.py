from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "EasyOrder"
    app_env: str = "local"
    backend_cors_origins: str = "http://localhost:5173"
    database_url: str = "postgresql://easyorder:easyorder@localhost:5432/easyorder"
    # "memory" keeps process-local stores; "postgres" persists sessions,
    # timeline events, and short links across restarts via DATABASE_URL.
    # Required outside local dev (enforced at startup in app.main).
    persistence_mode: str = "memory"
    # Shared asyncpg pool sizing for postgres mode.
    db_pool_min_size: int = 1
    db_pool_max_size: int = 10
    public_app_base_url: str = "http://localhost:5173"

    # WhatsApp
    whatsapp_verify_token: str = "local-verify-token"
    whatsapp_app_secret: str = ""
    whatsapp_provider_mode: str = "mock"
    whatsapp_access_token: str = ""
    whatsapp_phone_number_id: str = ""
    whatsapp_waba_id: str = ""
    whatsapp_api_version: str = "v20.0"
    # Approved handoff template; empty means use the interactive CTA message.
    whatsapp_handoff_template_name: str = ""
    whatsapp_handoff_template_language: str = "en"
    # Route untagged direct messages to the business number by intent.
    whatsapp_business_chat_enabled: bool = True

    # External integrations
    swiggy_client_mode: str = "mock"
    # URL of a real (or mock-but-networked) Swiggy MCP server, e.g.
    # http://localhost:9100/mcp for the local mock-swiggy-mcp service.
    swiggy_mcp_server_url: str = ""
    swiggy_mcp_auth_token: str = ""
    llm_mode: str = "mock"
    openai_api_key: str = ""
    openai_model: str = "gpt-4o-mini"
    # Poll interval for the SCHEDULED-order background placer.
    order_scheduler_poll_seconds: float = 30.0

    # Observability
    log_level: str = "INFO"
    # "text" is readable for local dev; use "json" in any hosted environment
    # so log lines are one JSON object per line for aggregators to parse.
    log_format: str = "text"
    sentry_dsn: str = ""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    @property
    def cors_origins(self) -> list[str]:
        return [origin.strip() for origin in self.backend_cors_origins.split(",") if origin.strip()]

    @property
    def skip_signature_verification(self) -> bool:
        """Skip webhook signature verification only in local dev with no secret configured."""
        return self.app_env == "local" and not self.whatsapp_app_secret


@lru_cache
def get_settings() -> Settings:
    return Settings()
