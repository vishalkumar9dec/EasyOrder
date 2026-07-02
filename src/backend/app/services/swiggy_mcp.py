"""Swiggy MCP client boundary and response normalization."""

from __future__ import annotations

import asyncio
import json
import os
import subprocess
from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from decimal import Decimal
from typing import Any, Protocol

from app.models.session import DietaryTag, Vertical
from app.services.mock_swiggy import MockSwiggyMcpClient
from app.services.protocols import ISwiggyMcpClient


class SwiggyMcpError(RuntimeError):
    """Base error raised when Swiggy MCP calls cannot be completed."""


class SwiggyMcpToolError(SwiggyMcpError):
    """Raised when an MCP tool returns or reports an error."""


class SwiggyMcpConfigurationError(SwiggyMcpError):
    """Raised when real Swiggy MCP mode is selected without configuration."""


class MCPToolRunner(Protocol):
    """Small abstraction for invoking one MCP tool."""

    async def call_tool(self, tool_name: str, arguments: Mapping[str, Any]) -> Mapping[str, Any]:
        """Invoke a tool and return its decoded JSON result."""
        ...


@dataclass(frozen=True)
class StdioMCPToolRunner:
    """Runs a configured MCP stdio command once per tool call.

    The runner expects the command to accept a JSON object on stdin containing
    ``tool`` and ``arguments``, then emit a JSON object on stdout.
    """

    server_path: str
    environment: Mapping[str, str] = field(default_factory=dict)
    timeout_seconds: float = 15

    async def call_tool(self, tool_name: str, arguments: Mapping[str, Any]) -> Mapping[str, Any]:
        if not self.server_path:
            raise SwiggyMcpConfigurationError("SWIGGY_MCP_SERVER_PATH is required")
        request = {"tool": tool_name, "arguments": dict(arguments)}
        return await asyncio.to_thread(self._run, request)

    def _run(self, request: Mapping[str, Any]) -> Mapping[str, Any]:
        environment = os.environ | dict(self.environment)
        try:
            result = subprocess.run(
                [self.server_path],
                input=json.dumps(request),
                capture_output=True,
                check=False,
                text=True,
                timeout=self.timeout_seconds,
                env=environment,
            )
        except OSError as error:
            raise SwiggyMcpConfigurationError("Swiggy MCP server could not be started") from error
        except subprocess.TimeoutExpired as error:
            raise SwiggyMcpToolError("Swiggy MCP tool call timed out") from error

        if result.returncode != 0:
            raise SwiggyMcpToolError("Swiggy MCP tool call failed")
        try:
            payload = json.loads(result.stdout or "{}")
        except json.JSONDecodeError as error:
            raise SwiggyMcpToolError("Swiggy MCP tool returned invalid JSON") from error
        if not isinstance(payload, dict):
            raise SwiggyMcpToolError("Swiggy MCP tool returned a non-object payload")
        return payload


class SwiggyMcpClient(ISwiggyMcpClient):
    """Production Swiggy MCP client with normalized EasyOrder responses."""

    def __init__(self, runner: MCPToolRunner) -> None:
        self.runner = runner

    async def search_restaurants(
        self,
        lat: float,
        lng: float,
        query: str,
    ) -> list[dict[str, Any]]:
        response = await self._call(
            "search_restaurants",
            {"lat": lat, "lng": lng, "query": query},
        )
        return [normalize_food_item(item) for item in extract_items(response)]

    async def get_restaurant_menu(self, restaurant_id: str) -> list[dict[str, Any]]:
        response = await self._call("get_restaurant_menu", {"restaurant_id": restaurant_id})
        return [
            normalize_food_item(item, default_restaurant_id=restaurant_id)
            for item in extract_items(response)
        ]

    async def search_instamart(
        self,
        lat: float,
        lng: float,
        query: str,
    ) -> list[dict[str, Any]]:
        response = await self._call("search_instamart", {"lat": lat, "lng": lng, "query": query})
        return [normalize_instamart_item(item) for item in extract_items(response)]

    async def exchange_oauth_code(self, oauth_code: str) -> str:
        response = await self._call("exchange_oauth_code", {"oauth_code": oauth_code})
        token = response.get("access_token") or response.get("token")
        if not token:
            raise SwiggyMcpToolError("Swiggy OAuth response did not include an access token")
        return f"Bearer {token}"

    async def create_cart(
        self,
        auth_header: str,
        vertical: str,
        items: list[dict[str, Any]],
    ) -> dict[str, Any]:
        response = await self._call(
            "create_cart",
            {
                "auth_header": auth_header,
                "vertical": vertical,
                "items": items,
            },
        )
        checkout_url = response.get("checkout_url") or response.get("url")
        if not checkout_url:
            raise SwiggyMcpToolError("Swiggy cart response did not include a checkout URL")
        return {
            "status": str(response.get("status") or "created"),
            "vertical": vertical,
            "checkout_url": str(checkout_url),
        }

    async def get_substitute_items(self, item_id: str) -> list[dict[str, Any]]:
        response = await self._call("get_substitute_items", {"item_id": item_id})
        return [normalize_instamart_item(item) for item in extract_items(response)]

    async def _call(self, tool_name: str, arguments: Mapping[str, Any]) -> Mapping[str, Any]:
        try:
            response = await self.runner.call_tool(tool_name, arguments)
        except SwiggyMcpError:
            raise
        except Exception as error:
            raise SwiggyMcpToolError(f"Swiggy MCP tool {tool_name} failed") from error
        if response.get("error"):
            raise SwiggyMcpToolError(f"Swiggy MCP tool {tool_name} returned an error")
        result = response.get("result", response)
        if not isinstance(result, Mapping):
            raise SwiggyMcpToolError(f"Swiggy MCP tool {tool_name} returned an invalid result")
        return result


def extract_items(response: Mapping[str, Any]) -> Sequence[Mapping[str, Any]]:
    raw_items = response.get("items") or response.get("results") or response.get("data") or []
    if not isinstance(raw_items, Sequence) or isinstance(raw_items, str | bytes):
        raise SwiggyMcpToolError("Swiggy MCP list response was not an array")
    return [item for item in raw_items if isinstance(item, Mapping)]


def normalize_food_item(
    item: Mapping[str, Any],
    default_restaurant_id: str | None = None,
) -> dict[str, Any]:
    restaurant = item.get("restaurant") if isinstance(item.get("restaurant"), Mapping) else {}
    restaurant_id = first_string(
        item.get("restaurant_id"),
        restaurant.get("id"),
        default_restaurant_id,
    )
    restaurant_name = first_string(item.get("restaurant_name"), restaurant.get("name"))
    if not restaurant_id or not restaurant_name:
        raise SwiggyMcpToolError("Food response is missing restaurant source attribution")
    return {
        "item_id": required_string(item, "item_id", "id", "sku"),
        "name": required_string(item, "name", "title"),
        "price": normalize_price(item.get("price") or item.get("price_rupees")),
        "dietary_tag": normalize_dietary_tag(item.get("dietary_tag") or item.get("diet")),
        "vertical": Vertical.FOOD,
        "source": "swiggy_mcp",
        "restaurant_id": restaurant_id,
        "restaurant_name": restaurant_name,
    }


def normalize_instamart_item(item: Mapping[str, Any]) -> dict[str, Any]:
    store = item.get("store") if isinstance(item.get("store"), Mapping) else {}
    source_label = first_string(item.get("source_label"), item.get("store_name"), store.get("name"))
    if not source_label:
        raise SwiggyMcpToolError("Instamart response is missing source attribution")
    return {
        "item_id": required_string(item, "item_id", "id", "sku"),
        "name": required_string(item, "name", "title"),
        "price": normalize_price(item.get("price") or item.get("price_rupees")),
        "dietary_tag": normalize_dietary_tag(item.get("dietary_tag") or item.get("diet")),
        "vertical": Vertical.INSTAMART,
        "source": "swiggy_mcp",
        "brand_name": first_string(item.get("brand_name"), item.get("brand")),
        "source_label": source_label,
    }


def required_string(item: Mapping[str, Any], *keys: str) -> str:
    value = first_string(*(item.get(key) for key in keys))
    if not value:
        raise SwiggyMcpToolError(f"Swiggy response is missing {keys[0]}")
    return value


def first_string(*values: object) -> str | None:
    for value in values:
        if value is None:
            continue
        text = str(value).strip()
        if text:
            return text
    return None


def normalize_price(value: object) -> str:
    if value is None:
        raise SwiggyMcpToolError("Swiggy response is missing price")
    return str(Decimal(str(value)).quantize(Decimal("0.01")))


def normalize_dietary_tag(value: object) -> DietaryTag:
    text = str(value or "ANY").upper().replace("_", "-")
    if text in {"VEG", "VEGETARIAN"}:
        return DietaryTag.VEG
    if text in {"NON-VEG", "NONVEG", "NON VEGETARIAN"}:
        return DietaryTag.NON_VEG
    return DietaryTag.ANY


def create_swiggy_client(
    *,
    mode: str,
    server_path: str,
    server_env: str = "{}",
) -> ISwiggyMcpClient:
    if mode == "mcp":
        if not server_path:
            raise SwiggyMcpConfigurationError("SWIGGY_MCP_SERVER_PATH is required in mcp mode")
        return SwiggyMcpClient(
            StdioMCPToolRunner(
                server_path=server_path,
                environment=parse_server_env(server_env),
            )
        )
    return MockSwiggyMcpClient()


def parse_server_env(raw_env: str) -> dict[str, str]:
    try:
        payload = json.loads(raw_env or "{}")
    except json.JSONDecodeError as error:
        raise SwiggyMcpConfigurationError("SWIGGY_MCP_SERVER_ENV must be JSON") from error
    if not isinstance(payload, dict):
        raise SwiggyMcpConfigurationError("SWIGGY_MCP_SERVER_ENV must be a JSON object")
    return {str(key): str(value) for key, value in payload.items()}
