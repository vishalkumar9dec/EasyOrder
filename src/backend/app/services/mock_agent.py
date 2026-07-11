"""Mock service implementations for local webhook development."""

from __future__ import annotations

from app.services.agent import EasyOrderAgentService
from app.services.memory_db import InMemoryDBAdapter
from app.services.mock_swiggy import MockSwiggyMcpClient
from app.services.protocols import IDBAdapter


class MockAgentService(EasyOrderAgentService):
    """Local EasyOrder agent using mock Swiggy; persistence is injectable."""

    def __init__(self, store: IDBAdapter | None = None) -> None:
        self.store = store or InMemoryDBAdapter()
        super().__init__(
            db=self.store,
            swiggy_client=MockSwiggyMcpClient(),
        )
