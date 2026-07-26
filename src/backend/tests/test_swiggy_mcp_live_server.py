"""End-to-end test against the real, running mock-swiggy-mcp service.

Spawns services/mock-swiggy-mcp/app/server.py as its own process (the exact
entrypoint used in production/Docker) and drives it through HttpMCPToolRunner
+ SwiggyMcpClient exactly as EasyOrder's backend would in mcp mode. Proves
the backend's MCP client and the independent mock server are wire-compatible
over a real HTTP connection, not just against a FakeRunner double.
"""

from __future__ import annotations

import asyncio
import socket
import subprocess
import sys
import time
from collections.abc import Iterator
from pathlib import Path

import pytest

from app.services.swiggy_mcp import HttpMCPToolRunner, SwiggyMcpClient


def run(coro):
    return asyncio.run(coro)

SERVER_SCRIPT = (
    Path(__file__).resolve().parents[3] / "services" / "mock-swiggy-mcp" / "app" / "server.py"
)
AUTH_TOKEN = "test-token"

pytestmark = pytest.mark.skipif(
    not SERVER_SCRIPT.exists(),
    reason="services/mock-swiggy-mcp is not present in this checkout",
)


def _free_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.bind(("127.0.0.1", 0))
        return sock.getsockname()[1]


@pytest.fixture
def server_url() -> Iterator[str]:
    port = _free_port()
    process = subprocess.Popen(
        [sys.executable, str(SERVER_SCRIPT)],
        env={
            "MOCK_MCP_AUTH_TOKEN": AUTH_TOKEN,
            "MOCK_MCP_HOST": "127.0.0.1",
            "MOCK_MCP_PORT": str(port),
            "PATH": "/usr/bin:/bin",
        },
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
    )
    try:
        _wait_for_startup(process)
        yield f"http://127.0.0.1:{port}/mcp"
    finally:
        process.terminate()
        process.wait(timeout=5)


def _wait_for_startup(process: subprocess.Popen, timeout: float = 10) -> None:
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if process.poll() is not None:
            raise RuntimeError(f"mock MCP server exited early:\n{process.stdout.read()}")
        line = process.stdout.readline()
        if "Application startup complete" in line:
            return
    raise TimeoutError("mock MCP server did not start in time")


def test_backend_client_talks_to_the_real_mock_mcp_server(server_url: str) -> None:
    client = SwiggyMcpClient(HttpMCPToolRunner(server_url=server_url, auth_token=AUTH_TOKEN))

    async def scenario():
        restaurants = await client.get_restaurants(12.9, 77.5)
        assert restaurants
        assert restaurants[0]["restaurant_id"]

        auth_header = await client.exchange_oauth_code("any-code")
        order = await client.place_order(
            auth_header,
            "food",
            restaurants[0]["restaurant_id"],
            [{"item_id": "food-1", "price": "100.00"}],
        )
        assert order["status"] == "placed"

        current = await client.get_current_order(auth_header, order["order_id"])
        assert current["status"] == "placed"

        history = await client.get_order_history(auth_header)
        assert history[0]["order_id"] == order["order_id"]

    run(scenario())


def test_backend_client_resolves_restaurant_by_name_against_the_real_mock_mcp_server(
    server_url: str,
) -> None:
    """find_restaurant_by_name/match_menu_items are client-side only (no new
    MCP tool) — this proves that still works over a real HTTP connection to
    the independent mock-swiggy-mcp process, not just a FakeRunner double."""
    client = SwiggyMcpClient(HttpMCPToolRunner(server_url=server_url, auth_token=AUTH_TOKEN))

    async def scenario():
        restaurant = await client.find_restaurant_by_name("motimahal")
        assert restaurant is not None
        assert restaurant["restaurant_id"] == "rest-moti-mahal"

        missing = await client.find_restaurant_by_name("no such restaurant")
        assert missing is None

        matched = await client.match_menu_items(
            "rest-moti-mahal", ["paneer tikka", "chicken 65", "nonexistent dish"]
        )
        assert {item["name"] for item in matched} == {"Paneer Tikka", "Chicken 65"}

    run(scenario())


def test_backend_client_rejects_wrong_auth_token(server_url: str) -> None:
    client = SwiggyMcpClient(HttpMCPToolRunner(server_url=server_url, auth_token="wrong-token"))

    with pytest.raises(Exception):  # noqa: B017 - transport wraps the 401 as an ExceptionGroup
        run(client.get_restaurants(12.9, 77.5))
