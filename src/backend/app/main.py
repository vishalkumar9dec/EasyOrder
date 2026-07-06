import logging
import re
import time
from datetime import UTC, datetime
from uuid import uuid4

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.session import router as session_router
from app.api.whatsapp import create_agent_service
from app.api.whatsapp import router as whatsapp_router
from app.config import get_settings
from app.services.whatsapp_sender import create_whatsapp_sender

logger = logging.getLogger("easyorder.api")
SESSION_PATH_RE = re.compile(r"/session/(?P<session_id>[^/?]+)")


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

    @app.middleware("http")
    async def request_logging(request, call_next):
        request_id = request.headers.get("x-request-id") or f"req_{uuid4().hex[:12]}"
        started = time.perf_counter()
        response = await call_next(request)
        elapsed_ms = round((time.perf_counter() - started) * 1000, 2)
        session_match = SESSION_PATH_RE.search(request.url.path)
        log_timestamp = datetime.now(UTC).isoformat()
        session_id = session_match.group("session_id") if session_match else None
        logger.info(
            (
                "request_complete "
                "timestamp=%s request_id=%s method=%s path=%s status_code=%s "
                "latency_ms=%s session_id=%s"
            ),
            log_timestamp,
            request_id,
            request.method,
            request.url.path,
            response.status_code,
            elapsed_ms,
            session_id,
            extra={
                "timestamp": log_timestamp,
                "request_id": request_id,
                "method": request.method,
                "path": request.url.path,
                "status_code": response.status_code,
                "latency_ms": elapsed_ms,
                "session_id": session_id,
            },
        )
        response.headers["x-request-id"] = request_id
        return response

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
