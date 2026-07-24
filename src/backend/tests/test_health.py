from fastapi.testclient import TestClient

from app.config import Settings, get_settings
from app.main import app, create_app


def test_healthz_returns_deterministic_status() -> None:
    response = TestClient(app).get("/healthz")

    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_readyz_exposes_mock_dependency_modes() -> None:
    response = TestClient(app).get("/readyz")

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ready"
    assert body["whatsapp"] == "mock"
    assert body["swiggy"] == "mock"
    assert body["llm"] == "mock"
    # Mock modes need no external credential, so they always report configured.
    assert body["whatsapp_configured"] is True
    assert body["swiggy_configured"] is True
    assert body["llm_configured"] is True


def test_metrics_endpoint_exposes_prometheus_text_format() -> None:
    client = TestClient(app)
    client.get("/healthz")

    response = client.get("/metrics")

    assert response.status_code == 200
    assert "text/plain" in response.headers["content-type"]
    assert "easyorder_http_requests_total" in response.text


def test_webhook_events_counter_increments_on_real_webhook_traffic() -> None:
    client = TestClient(app)
    client.get("/healthz", headers={"x-request-id": "warm-up"})  # ensure metric family exists

    client.post("/api/whatsapp/webhook", json={"object": "whatsapp_business_account", "entry": []})
    response = client.get("/metrics")

    assert 'easyorder_webhook_events_total{event="whatsapp_webhook_received"}' in response.text


def test_request_logging_middleware_sets_request_id_header() -> None:
    response = TestClient(app).get("/healthz", headers={"x-request-id": "req_test_123"})

    assert response.status_code == 200
    assert response.headers["x-request-id"] == "req_test_123"


def test_request_logging_middleware_logs_timestamp(caplog) -> None:
    with caplog.at_level("INFO", logger="easyorder.api"):
        response = TestClient(app).get("/healthz", headers={"x-request-id": "req_test_456"})

    assert response.status_code == 200
    request_log = next(
        record for record in caplog.records if record.message.startswith("request_complete")
    )
    assert "timestamp=" in request_log.message
    assert "req_test_456" in request_log.message
    assert request_log.timestamp.endswith("+00:00")


def test_readyz_reports_swiggy_mcp_mode_as_configured_when_url_is_set(monkeypatch) -> None:
    monkeypatch.setenv("APP_ENV", "local")
    monkeypatch.setenv("PERSISTENCE_MODE", "memory")
    monkeypatch.setenv("WHATSAPP_PROVIDER_MODE", "mock")
    monkeypatch.setenv("SWIGGY_CLIENT_MODE", "mcp")
    monkeypatch.setenv("SWIGGY_MCP_SERVER_URL", "http://localhost:9100/mcp")
    get_settings.cache_clear()

    try:
        response = TestClient(create_app()).get("/readyz")
    finally:
        get_settings.cache_clear()

    body = response.json()
    assert body["swiggy"] == "mcp"
    assert body["swiggy_configured"] is True


def test_settings_parses_comma_separated_cors_origins() -> None:
    settings = Settings(backend_cors_origins="http://localhost:5173,http://localhost:4173")

    assert settings.cors_origins == ["http://localhost:5173", "http://localhost:4173"]
