"""Structured logging, request/event metrics, and optional error tracking.

Addresses the production-readiness gap: "Logging is unconfigured (no level/
format/JSON); no metrics ... and no error tracking" (docs/production-readiness.md).
"""

from __future__ import annotations

import json
import logging
import time
from collections.abc import Awaitable, Callable

from prometheus_client import CONTENT_TYPE_LATEST, Counter, Histogram, generate_latest
from starlette.requests import Request
from starlette.responses import Response

# Attributes every stdlib LogRecord already carries; anything else on the
# record came from a caller's `extra={...}` and belongs in the JSON payload.
_STANDARD_RECORD_ATTRS = frozenset(logging.makeLogRecord({}).__dict__.keys())


class JsonFormatter(logging.Formatter):
    """One JSON object per log line: timestamp, level, logger, message, and
    any caller-supplied `extra` fields merged in directly (not nested)."""

    def format(self, record: logging.LogRecord) -> str:
        payload: dict[str, object] = {
            "timestamp": self.formatTime(record, "%Y-%m-%dT%H:%M:%S%z"),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        for key, value in record.__dict__.items():
            if key not in _STANDARD_RECORD_ATTRS:
                payload[key] = value
        if record.exc_info:
            payload["exception"] = self.formatException(record.exc_info)
        return json.dumps(payload, default=str)


def configure_logging(*, level: str, log_format: str) -> None:
    """Configure the root logger once at startup.

    log_format="json" emits one JSON object per line (for log aggregators);
    anything else keeps a readable plain-text format for local development.
    """
    root = logging.getLogger()
    root.setLevel(level.upper())
    handler = logging.StreamHandler()
    if log_format == "json":
        handler.setFormatter(JsonFormatter())
    else:
        handler.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(name)s %(message)s"))
    root.handlers = [handler]


def init_error_tracking(*, dsn: str, environment: str) -> None:
    """Initialize Sentry error tracking; a no-op when no DSN is configured."""
    if not dsn:
        return
    import sentry_sdk

    sentry_sdk.init(dsn=dsn, environment=environment)


HTTP_REQUESTS_TOTAL = Counter(
    "easyorder_http_requests_total",
    "Total HTTP requests handled, labeled by route and status code.",
    ["method", "path", "status"],
)
HTTP_REQUEST_DURATION_SECONDS = Histogram(
    "easyorder_http_request_duration_seconds",
    "HTTP request duration in seconds, labeled by route.",
    ["method", "path"],
)
WEBHOOK_EVENTS_TOTAL = Counter(
    "easyorder_webhook_events_total",
    "WhatsApp webhook events processed, labeled by event name.",
    ["event"],
)
AGENT_ERRORS_TOTAL = Counter(
    "easyorder_agent_errors_total",
    "Agent graph node failures, labeled by node name.",
    ["node"],
)


async def metrics_middleware(
    request: Request, call_next: Callable[[Request], Awaitable[Response]]
) -> Response:
    """Records request count and latency. Uses the matched route template
    (e.g. /api/session/{session_id}), not the raw path, so metric label
    cardinality stays bounded regardless of how many distinct sessions exist."""
    start = time.monotonic()
    response = await call_next(request)
    duration = time.monotonic() - start

    route = request.scope.get("route")
    path = getattr(route, "path", request.url.path)
    HTTP_REQUESTS_TOTAL.labels(
        method=request.method, path=path, status=str(response.status_code)
    ).inc()
    HTTP_REQUEST_DURATION_SECONDS.labels(method=request.method, path=path).observe(duration)
    return response


def metrics_endpoint() -> Response:
    """Handler for GET /metrics — Prometheus text exposition format."""
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)


__all__ = [
    "AGENT_ERRORS_TOTAL",
    "WEBHOOK_EVENTS_TOTAL",
    "configure_logging",
    "init_error_tracking",
    "metrics_endpoint",
    "metrics_middleware",
]
