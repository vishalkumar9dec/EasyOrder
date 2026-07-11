from fastapi.testclient import TestClient

from app.main import app
from app.services.short_links import InMemoryShortLinkService


def test_short_link_service_creates_opaque_reusable_codes() -> None:
    service = InMemoryShortLinkService()

    code = service.create("/session/session_abc?token=guest_secret")
    repeat = service.create("/session/session_abc?token=guest_secret")
    other = service.create("/session/session_xyz?token=guest_other")

    assert code == repeat
    assert code != other
    assert "guest_secret" not in code
    assert "session_abc" not in code
    assert service.resolve(code) == "/session/session_abc?token=guest_secret"
    assert service.resolve("unknown") is None


def test_short_link_service_rejects_absolute_targets() -> None:
    service = InMemoryShortLinkService()

    try:
        service.create("https://evil.example/session/x?token=guest_y")
    except ValueError:
        pass
    else:
        raise AssertionError("absolute target was accepted")


def test_short_link_service_builds_absolute_short_url() -> None:
    service = InMemoryShortLinkService()

    url = service.create_short_url("http://localhost:5173/", "/session/s1?token=guest_t1")

    assert url.startswith("http://localhost:5173/api/r/")
    assert "token=" not in url


def test_redirect_endpoint_resolves_known_code() -> None:
    client = TestClient(app)
    service: InMemoryShortLinkService = app.state.short_links
    code = service.create("/session/session_redirect?token=guest_redirect")

    response = client.get(f"/api/r/{code}", follow_redirects=False)

    assert response.status_code == 307
    assert response.headers["location"].endswith(
        "/session/session_redirect?token=guest_redirect"
    )


def test_redirect_endpoint_rejects_unknown_code() -> None:
    response = TestClient(app).get("/api/r/does-not-exist", follow_redirects=False)

    assert response.status_code == 404
    assert response.json()["detail"] == "Unknown or expired link"
