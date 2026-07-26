"""Swiggy MCP client boundary and response normalization."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from decimal import Decimal
from typing import Any, Protocol

from mcp import ClientSession
from mcp.client.streamable_http import streamablehttp_client

from app.models.session import DietaryTag, Vertical
from app.services import menu_matching
from app.services.mock_swiggy import MockSwiggyMcpClient
from app.services.protocols import ISwiggyMcpClient

DEFAULT_LAT = 12.9716
DEFAULT_LNG = 77.5946


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


class HttpMCPToolRunner:
    """Calls tools on a real MCP server over Streamable HTTP.

    This is how EasyOrder would consume a real vendor-hosted Swiggy MCP
    endpoint: a URL plus a bearer token, nothing shared in-process. Opens one
    MCP session per tool call — simple and correct for this call volume; a
    persistent session can be introduced later if latency becomes an issue.
    """

    def __init__(self, server_url: str, auth_token: str = "", timeout_seconds: float = 15) -> None:
        self.server_url = server_url
        self.auth_token = auth_token
        self.timeout_seconds = timeout_seconds

    async def call_tool(self, tool_name: str, arguments: Mapping[str, Any]) -> Mapping[str, Any]:
        if not self.server_url:
            raise SwiggyMcpConfigurationError("SWIGGY_MCP_SERVER_URL is required")
        headers = {"Authorization": f"Bearer {self.auth_token}"} if self.auth_token else None
        try:
            async with streamablehttp_client(
                self.server_url, headers=headers, timeout=self.timeout_seconds
            ) as (read, write, _):
                async with ClientSession(read, write) as session:
                    await session.initialize()
                    result = await session.call_tool(tool_name, dict(arguments))
        except SwiggyMcpError:
            raise
        except Exception as error:
            raise SwiggyMcpConfigurationError(
                f"Swiggy MCP server at {self.server_url} could not be reached"
            ) from error

        if result.isError:
            raise SwiggyMcpToolError(f"Swiggy MCP tool {tool_name} reported an error")
        if result.structuredContent is None:
            raise SwiggyMcpToolError(f"Swiggy MCP tool {tool_name} returned no structured content")
        return result.structuredContent


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

    async def get_restaurants(self, lat: float, lng: float) -> list[dict[str, Any]]:
        response = await self._call("get_restaurants", {"lat": lat, "lng": lng})
        return [normalize_restaurant(item) for item in extract_items(response)]

    async def get_restaurant(self, restaurant_id: str) -> dict[str, Any]:
        response = await self._call("get_restaurant", {"restaurant_id": restaurant_id})
        return normalize_restaurant(response)

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

    async def find_restaurant_by_name(self, name: str) -> dict[str, Any] | None:
        restaurants = await self.get_restaurants(DEFAULT_LAT, DEFAULT_LNG)
        return menu_matching.find_restaurant_by_name(restaurants, name)

    async def match_menu_items(
        self,
        restaurant_id: str,
        dish_names: Sequence[str],
    ) -> list[dict[str, Any]]:
        menu = await self.get_restaurant_menu(restaurant_id)
        return menu_matching.match_menu_items(menu, dish_names)

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

    async def place_order(
        self,
        auth_header: str,
        vertical: str,
        restaurant_id: str,
        items: list[dict[str, Any]],
    ) -> dict[str, Any]:
        response = await self._call(
            "place_order",
            {
                "auth_header": auth_header,
                "vertical": vertical,
                "restaurant_id": restaurant_id,
                "items": items,
            },
        )
        return normalize_order(response)

    async def get_order_history(self, auth_header: str) -> list[dict[str, Any]]:
        response = await self._call("get_order_history", {"auth_header": auth_header})
        return [normalize_order(item) for item in extract_items(response)]

    async def get_current_order(self, auth_header: str, order_id: str) -> dict[str, Any]:
        response = await self._call(
            "get_current_order",
            {"auth_header": auth_header, "order_id": order_id},
        )
        return normalize_order(response)

    async def get_delivery_update(self, order_id: str) -> dict[str, Any]:
        response = await self._call("get_delivery_update", {"order_id": order_id})
        return {
            "order_id": required_string(response, "order_id"),
            "status": required_string(response, "status"),
            "eta_minutes": int(response.get("eta_minutes") or 0),
            "rider_name": first_string(response.get("rider_name")),
        }

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


def normalize_restaurant(item: Mapping[str, Any]) -> dict[str, Any]:
    return {
        "restaurant_id": required_string(item, "restaurant_id", "id"),
        "name": required_string(item, "name", "title"),
        "cuisines": [str(c) for c in item.get("cuisines") or []],
        "rating": float(item.get("rating") or 0.0),
        "eta_minutes": int(item.get("eta_minutes") or 0),
    }


def normalize_order(item: Mapping[str, Any]) -> dict[str, Any]:
    return {
        "order_id": required_string(item, "order_id", "id"),
        "vertical": required_string(item, "vertical"),
        "restaurant_id": first_string(item.get("restaurant_id")),
        "items": list(item.get("items") or []),
        "total": normalize_price(item.get("total")),
        "status": required_string(item, "status"),
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
    server_url: str,
    auth_token: str = "",
) -> ISwiggyMcpClient:
    if mode == "mcp":
        if not server_url:
            raise SwiggyMcpConfigurationError("SWIGGY_MCP_SERVER_URL is required in mcp mode")
        return SwiggyMcpClient(HttpMCPToolRunner(server_url=server_url, auth_token=auth_token))
    return MockSwiggyMcpClient()
