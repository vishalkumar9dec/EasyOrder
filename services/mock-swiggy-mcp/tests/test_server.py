"""End-to-end tests against the real, running mock Swiggy MCP server.

Spawns the actual uvicorn process (same entrypoint as production) and talks
to it with the real MCP client SDK over Streamable HTTP — this is the same
round trip EasyOrder's backend uses, just pointed at a test port.
"""

from __future__ import annotations

import socket
import subprocess
import sys
import time
import uuid
from collections.abc import AsyncIterator
from pathlib import Path

import pytest
from mcp.client.session import ClientSession
from mcp.client.streamable_http import streamablehttp_client

SERVER_SCRIPT = Path(__file__).parent.parent / "app" / "server.py"
AUTH_TOKEN = "test-token"


def _free_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.bind(("127.0.0.1", 0))
        return sock.getsockname()[1]


@pytest.fixture
def server_url() -> AsyncIterator[str]:
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
    url = f"http://127.0.0.1:{port}/mcp"
    try:
        _wait_for_startup(process)
        yield url
    finally:
        process.terminate()
        process.wait(timeout=5)


def _wait_for_startup(process: subprocess.Popen, timeout: float = 10) -> None:
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if process.poll() is not None:
            raise RuntimeError(f"server exited early:\n{process.stdout.read()}")
        line = process.stdout.readline()
        if "Application startup complete" in line:
            return
    raise TimeoutError("mock MCP server did not start in time")


async def call_tool(url: str, tool: str, arguments: dict, token: str = AUTH_TOKEN) -> object:
    async with streamablehttp_client(url, headers={"Authorization": f"Bearer {token}"}) as (
        read,
        write,
        _,
    ):
        async with ClientSession(read, write) as session:
            await session.initialize()
            return await session.call_tool(tool, arguments)


async def test_lists_tools_matching_the_swiggy_contract(server_url: str) -> None:
    async with streamablehttp_client(
        server_url, headers={"Authorization": f"Bearer {AUTH_TOKEN}"}
    ) as (read, write, _):
        async with ClientSession(read, write) as session:
            await session.initialize()
            tools = await session.list_tools()

    names = {tool.name for tool in tools.tools}
    assert names == {
        "get_restaurants",
        "get_restaurant",
        "search_restaurants",
        "get_restaurant_menu",
        "search_instamart",
        "get_substitute_items",
        "exchange_oauth_code",
        "create_cart",
        "place_order",
        "get_order_history",
        "get_current_order",
        "get_delivery_update",
    }


async def test_rejects_requests_without_a_valid_bearer_token(server_url: str) -> None:
    with pytest.raises(Exception):  # noqa: B017 - transport raises an ExceptionGroup on 401
        await call_tool(server_url, "get_restaurants", {"lat": 12.9, "lng": 77.5}, token="wrong")


async def test_get_restaurants_and_get_restaurant(server_url: str) -> None:
    restaurants = await call_tool(server_url, "get_restaurants", {"lat": 12.9, "lng": 77.5})
    items = restaurants.structuredContent["items"]
    assert items

    restaurant = await call_tool(server_url, "get_restaurant", {"restaurant_id": items[0]["id"]})
    assert restaurant.structuredContent["id"] == items[0]["id"]


async def test_order_lifecycle_progresses_deterministically(server_url: str) -> None:
    customer = f"Bearer {uuid.uuid4()}"

    placed = await call_tool(
        server_url,
        "place_order",
        {
            "auth_header": customer,
            "vertical": "food",
            "restaurant_id": "rest-biryani-house",
            "items": [{"item_id": "food-chicken-biryani", "price": "620.00"}],
        },
    )
    order = placed.structuredContent
    assert order["status"] == "placed"
    assert order["total"] == "620.00"
    order_id = order["order_id"]

    first_poll = await call_tool(
        server_url, "get_current_order", {"auth_header": customer, "order_id": order_id}
    )
    second_poll = await call_tool(
        server_url, "get_current_order", {"auth_header": customer, "order_id": order_id}
    )
    assert first_poll.structuredContent["status"] == "placed"
    assert second_poll.structuredContent["status"] == "preparing"

    history = await call_tool(server_url, "get_order_history", {"auth_header": customer})
    assert history.structuredContent["items"][0]["order_id"] == order_id

    other_customer = await call_tool(
        server_url,
        "get_current_order",
        {"auth_header": "Bearer someone-else", "order_id": order_id},
    )
    assert "error" in other_customer.structuredContent


async def test_delivery_update_reports_rider_only_when_out_for_delivery(server_url: str) -> None:
    customer = f"Bearer {uuid.uuid4()}"
    placed = await call_tool(
        server_url,
        "place_order",
        {"auth_header": customer, "vertical": "food", "restaurant_id": "rest-1", "items": []},
    )
    order_id = placed.structuredContent["order_id"]

    first = await call_tool(server_url, "get_delivery_update", {"order_id": order_id})
    second = await call_tool(server_url, "get_delivery_update", {"order_id": order_id})
    third = await call_tool(server_url, "get_delivery_update", {"order_id": order_id})

    assert first.structuredContent["rider_name"] is None
    assert second.structuredContent["rider_name"] is None
    assert third.structuredContent["status"] == "out_for_delivery"
    assert third.structuredContent["rider_name"] == "Mock Rider"
