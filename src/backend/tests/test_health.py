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


def test_settings_parses_comma_separated_cors_origins() -> None:
    settings = Settings(backend_cors_origins="http://localhost:5173,http://localhost:4173")

    assert settings.cors_origins == ["http://localhost:5173", "http://localhost:4173"]
