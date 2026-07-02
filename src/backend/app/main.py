from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.session import router as session_router
from app.api.whatsapp import create_agent_service
from app.api.whatsapp import router as whatsapp_router
from app.config import get_settings
from app.services.whatsapp_sender import create_whatsapp_sender


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(title=settings.app_name)
    app.state.agent_service = create_agent_service(settings)
    app.state.db_adapter = app.state.agent_service.db
    app.state.swiggy_client = app.state.agent_service.swiggy_client
    app.state.whatsapp_sender = create_whatsapp_sender(
        provider_mode=settings.whatsapp_provider_mode,
        access_token=settings.whatsapp_access_token,
        phone_number_id=settings.whatsapp_phone_number_id,
        api_version=settings.whatsapp_api_version,
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.get("/healthz")
    async def healthz() -> dict[str, str]:
        return {
            "status": "ok",
            "app": settings.app_name,
            "environment": settings.app_env,
        }

    @app.get("/readyz")
    async def readyz() -> dict[str, str]:
        return {
            "status": "ready",
            "database": "not_checked",
            "whatsapp": settings.whatsapp_provider_mode,
            "swiggy": settings.swiggy_client_mode,
            "llm": settings.llm_mode,
        }

    app.include_router(session_router)
    app.include_router(whatsapp_router)

    return app


app = create_app()
