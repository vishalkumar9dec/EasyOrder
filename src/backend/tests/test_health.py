from fastapi.testclient import TestClient

from app.config import Settings
from app.main import app


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


def test_request_logging_middleware_sets_request_id_header() -> None:
    response = TestClient(app).get("/healthz", headers={"x-request-id": "req_test_123"})

    assert response.status_code == 200
    assert response.headers["x-request-id"] == "req_test_123"


def test_request_logging_middleware_logs_timestamp(caplog) -> None:
    with caplog.at_level("INFO", logger="easyorder.api"):
        response = TestClient(app).get("/healthz", headers={"x-request-id": "req_test_456"})

    assert response.status_code == 200
    request_log = next(record for record in caplog.records if record.message.startswith("request_complete"))
    assert "timestamp=" in request_log.message
    assert "req_test_456" in request_log.message
    assert request_log.timestamp.endswith("+00:00")


def test_settings_parses_comma_separated_cors_origins() -> None:
    settings = Settings(backend_cors_origins="http://localhost:5173,http://localhost:4173")

    assert settings.cors_origins == ["http://localhost:5173", "http://localhost:4173"]
