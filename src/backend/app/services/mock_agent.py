"""Mock service implementations for local webhook development."""

from __future__ import annotations

from app.services.agent import EasyOrderAgentService, IntentParser
from app.services.memory_db import InMemoryDBAdapter
from app.services.mock_swiggy import MockSwiggyMcpClient
from app.services.protocols import IDBAdapter


class MockAgentService(EasyOrderAgentService):
    """Local EasyOrder agent using mock Swiggy; persistence and the intent
    parser are both injectable so LLM_MODE can be swapped independently of
    SWIGGY_CLIENT_MODE (e.g. real LLM parsing against a still-mocked Swiggy)."""

    def __init__(self, store: IDBAdapter | None = None, parser: IntentParser | None = None) -> None:
        self.store = store or InMemoryDBAdapter()
        super().__init__(
            db=self.store,
            swiggy_client=MockSwiggyMcpClient(),
            parser=parser,
        )
