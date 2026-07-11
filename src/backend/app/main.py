import logging
import re
import time
from datetime import UTC, datetime
from uuid import uuid4

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.account import router as account_router
from app.api.session import router as session_router
from app.api.short_links import router as short_links_router
from app.api.whatsapp import create_agent_service, create_db_adapter_for_settings
from app.api.whatsapp import router as whatsapp_router
from app.config import get_settings
from app.services.short_links import create_short_link_service
from app.services.web_auth import create_auth_store
from app.services.whatsapp_sender import create_whatsapp_sender

logger = logging.getLogger("easyorder.api")
SESSION_PATH_RE = re.compile(r"/session/(?P<session_id>[^/?]+)")


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(title=settings.app_name)
    db_adapter = create_db_adapter_for_settings(settings)
    app.state.agent_service = create_agent_service(settings, db=db_adapter)
    app.state.db_adapter = db_adapter
    app.state.swiggy_client = app.state.agent_service.swiggy_client
    app.state.whatsapp_sender = create_whatsapp_sender(
        provider_mode=settings.whatsapp_provider_mode,
        access_token=settings.whatsapp_access_token,
        phone_number_id=settings.whatsapp_phone_number_id,
        api_version=settings.whatsapp_api_version,
        handoff_template_name=settings.whatsapp_handoff_template_name,
        handoff_template_language=settings.whatsapp_handoff_template_language,
    )
    app.state.short_links = create_short_link_service(settings)
    app.state.auth_store = create_auth_store(settings)

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
        database_state = "memory"
        if settings.persistence_mode == "postgres":
            try:
                connection = await create_db_adapter_for_settings(
                    settings
                )._connection_factory()
                try:
                    await connection.fetchrow("SELECT 1 AS ok")
                    database_state = "postgres_ok"
                finally:
                    await connection.close()
            except Exception:
                logger.exception("readyz_database_check_failed")
                database_state = "postgres_error"
        return {
            "status": "ready",
            "database": database_state,
            "whatsapp": settings.whatsapp_provider_mode,
            "swiggy": settings.swiggy_client_mode,
            "llm": settings.llm_mode,
        }

    app.include_router(account_router)
    app.include_router(session_router)
    app.include_router(short_links_router)
    app.include_router(whatsapp_router)

    return app


app = create_app()
