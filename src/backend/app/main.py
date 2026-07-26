import asyncio
import contextlib
import logging
import re
import time
from contextlib import asynccontextmanager
from datetime import UTC, datetime
from uuid import uuid4

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.account import router as account_router
from app.api.dev_tools import router as dev_tools_router
from app.api.session import router as session_router
from app.api.short_links import router as short_links_router
from app.api.whatsapp import (
    create_agent_service,
    create_db_adapter_for_settings,
    create_targeted_order_service,
)
from app.api.whatsapp import router as whatsapp_router
from app.config import get_settings
from app.db.pool import AsyncpgConnectionPool
from app.observability import (
    configure_logging,
    init_error_tracking,
    metrics_endpoint,
    metrics_middleware,
)
from app.services.order_scheduler import OrderScheduler
from app.services.rate_limit import OtpRateLimiter
from app.services.short_links import create_short_link_service
from app.services.web_auth import create_auth_store
from app.services.whatsapp_sender import create_whatsapp_sender

logger = logging.getLogger("easyorder.api")
SESSION_PATH_RE = re.compile(r"/session/(?P<session_id>[^/?]+)")


def _mode_is_configured(mode: str, credential_required_mode: str, has_credential: bool) -> bool:
    """True if `mode` needs no external credential, or the credential it needs is present.

    Startup guards already refuse to boot in the missing-credential case for
    every integration below, so this is normally always True on a running
    instance — reported explicitly here so /readyz never has to be taken on
    faith (docs/production-readiness.md: "readyz reports mode strings
    without validating that credentials are present").
    """
    return mode != credential_required_mode or has_credential


def create_app() -> FastAPI:
    settings = get_settings()
    configure_logging(level=settings.log_level, log_format=settings.log_format)
    init_error_tracking(dsn=settings.sentry_dsn, environment=settings.app_env)

    # Fail closed: the real Meta provider must never run without an app secret,
    # otherwise webhook signature verification cannot be enforced. This makes a
    # production "meta" deploy without a secret impossible to boot, which in
    # turn guarantees signature checks are only ever skipped in local mock dev.
    if settings.whatsapp_provider_mode == "meta" and not settings.whatsapp_app_secret:
        raise RuntimeError("WHATSAPP_APP_SECRET must be set when WHATSAPP_PROVIDER_MODE=meta")
    if settings.skip_signature_verification:
        logger.warning(
            "webhook_signature_verification_disabled app_env=%s provider=%s",
            settings.app_env,
            settings.whatsapp_provider_mode,
        )

    # Durable persistence is required outside local dev: memory mode loses
    # sessions, carts, timeline, OTPs, logins, and short links on restart and
    # cannot be shared across instances.
    if settings.app_env != "local" and settings.persistence_mode != "postgres":
        raise RuntimeError(
            "PERSISTENCE_MODE=postgres is required when app_env is not local "
            f"(got app_env={settings.app_env!r}, persistence_mode={settings.persistence_mode!r})"
        )

    # Fail closed: LLM_MODE=openai without a key would silently fall back to
    # the mock parser on every single message (LLMIntentParser's runtime
    # fallback) rather than actually doing real parsing. Catch the
    # misconfiguration at startup instead of discovering it in production logs.
    if settings.llm_mode == "openai" and not settings.openai_api_key:
        raise RuntimeError("OPENAI_API_KEY must be set when LLM_MODE=openai")

    # One shared asyncpg pool for the whole process, threaded into every
    # Postgres-backed store. None in memory mode.
    db_pool: AsyncpgConnectionPool | None = None
    connection_factory = None
    if settings.persistence_mode == "postgres":
        db_pool = AsyncpgConnectionPool(
            settings.database_url,
            min_size=settings.db_pool_min_size,
            max_size=settings.db_pool_max_size,
        )
        connection_factory = db_pool.connection_factory()

    @asynccontextmanager
    async def lifespan(_app: FastAPI):
        scheduler_task = asyncio.create_task(_app.state.order_scheduler.run_forever())
        try:
            yield
        finally:
            scheduler_task.cancel()
            with contextlib.suppress(asyncio.CancelledError):
                await scheduler_task
            if db_pool is not None:
                await db_pool.close()

    app = FastAPI(title=settings.app_name, lifespan=lifespan)
    db_adapter = create_db_adapter_for_settings(settings, connection_factory)
    app.state.agent_service = create_agent_service(settings, db=db_adapter)
    app.state.db_adapter = db_adapter
    app.state.db_pool = db_pool
    app.state.swiggy_client = app.state.agent_service.swiggy_client
    app.state.targeted_order_service = create_targeted_order_service(
        settings, db_adapter, app.state.swiggy_client
    )
    app.state.whatsapp_sender = create_whatsapp_sender(
        provider_mode=settings.whatsapp_provider_mode,
        access_token=settings.whatsapp_access_token,
        phone_number_id=settings.whatsapp_phone_number_id,
        api_version=settings.whatsapp_api_version,
        handoff_template_name=settings.whatsapp_handoff_template_name,
        handoff_template_language=settings.whatsapp_handoff_template_language,
    )
    app.state.order_scheduler = OrderScheduler(
        db=db_adapter,
        swiggy_client=app.state.swiggy_client,
        whatsapp_sender=app.state.whatsapp_sender,
        poll_interval_seconds=settings.order_scheduler_poll_seconds,
    )
    app.state.short_links = create_short_link_service(settings, connection_factory)
    app.state.auth_store = create_auth_store(settings, connection_factory)
    app.state.otp_rate_limiter = OtpRateLimiter()

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.middleware("http")(metrics_middleware)

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

    @app.get("/metrics")
    async def metrics():
        return metrics_endpoint()

    @app.get("/readyz")
    async def readyz() -> dict[str, str | bool]:
        database_state = "memory"
        if settings.persistence_mode == "postgres" and connection_factory is not None:
            try:
                connection = await connection_factory()
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
            "whatsapp_configured": _mode_is_configured(
                settings.whatsapp_provider_mode,
                "meta",
                bool(settings.whatsapp_access_token and settings.whatsapp_phone_number_id),
            ),
            "swiggy": settings.swiggy_client_mode,
            "swiggy_configured": _mode_is_configured(
                settings.swiggy_client_mode, "mcp", bool(settings.swiggy_mcp_server_url)
            ),
            "llm": settings.llm_mode,
            "llm_configured": _mode_is_configured(
                settings.llm_mode, "openai", bool(settings.openai_api_key)
            ),
        }

    app.include_router(account_router)
    app.include_router(dev_tools_router)
    app.include_router(session_router)
    app.include_router(short_links_router)
    app.include_router(whatsapp_router)

    return app


app = create_app()
