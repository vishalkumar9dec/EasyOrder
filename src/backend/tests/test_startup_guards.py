"""create_app() fail-closed guards for production misconfiguration."""

import pytest

from app.config import get_settings
from app.db.pool import AsyncpgConnectionPool
from app.main import create_app


def _set_env(monkeypatch, **env: str) -> None:
    for key, value in env.items():
        monkeypatch.setenv(key, value)
    get_settings.cache_clear()


def test_non_local_env_requires_postgres(monkeypatch) -> None:
    try:
        _set_env(
            monkeypatch,
            APP_ENV="production",
            PERSISTENCE_MODE="memory",
            WHATSAPP_PROVIDER_MODE="mock",
        )
        with pytest.raises(RuntimeError, match="PERSISTENCE_MODE=postgres"):
            create_app()
    finally:
        get_settings.cache_clear()


def test_meta_provider_requires_app_secret(monkeypatch) -> None:
    try:
        _set_env(
            monkeypatch,
            APP_ENV="local",
            PERSISTENCE_MODE="memory",
            WHATSAPP_PROVIDER_MODE="meta",
            WHATSAPP_APP_SECRET="",
        )
        with pytest.raises(RuntimeError, match="WHATSAPP_APP_SECRET"):
            create_app()
    finally:
        get_settings.cache_clear()


def test_non_local_postgres_boots_without_connecting(monkeypatch) -> None:
    try:
        _set_env(
            monkeypatch,
            APP_ENV="production",
            PERSISTENCE_MODE="postgres",
            WHATSAPP_PROVIDER_MODE="mock",
            DATABASE_URL="postgresql://user:pass@localhost:5432/db",
        )
        app = create_app()
        # Pool is created but lazy — no DB connection is opened at startup.
        assert isinstance(app.state.db_pool, AsyncpgConnectionPool)
    finally:
        get_settings.cache_clear()
