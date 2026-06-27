from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import get_settings


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(title=settings.app_name)

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

    return app


app = create_app()
