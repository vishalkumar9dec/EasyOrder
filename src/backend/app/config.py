from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "EasyOrder"
    app_env: str = "local"
    backend_cors_origins: str = "http://localhost:5173"
    database_url: str = "postgresql://easyorder:easyorder@localhost:5432/easyorder"
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

    # External integrations
    swiggy_client_mode: str = "mock"
    swiggy_mcp_server_path: str = ""
    swiggy_mcp_server_env: str = "{}"
    llm_mode: str = "mock"

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
