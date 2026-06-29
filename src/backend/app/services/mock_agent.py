"""Mock service implementations for local webhook development."""

from __future__ import annotations

from app.services.agent import EasyOrderAgentService
from app.services.memory_db import InMemoryDBAdapter
from app.services.mock_swiggy import MockSwiggyMcpClient


class MockAgentService(EasyOrderAgentService):
    """Local EasyOrder agent backed by in-memory persistence and mock Swiggy."""

    def __init__(self, store: InMemoryDBAdapter | None = None) -> None:
        self.store = store or InMemoryDBAdapter()
        super().__init__(
            db=self.store,
            swiggy_client=MockSwiggyMcpClient(),
        )
