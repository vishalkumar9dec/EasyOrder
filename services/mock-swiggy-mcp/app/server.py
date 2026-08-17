"""Mock Swiggy MCP server.

A genuine MCP-protocol server (official `mcp` SDK, Streamable HTTP
transport) that stands in for a real Swiggy-hosted MCP endpoint. It is a
separate, independently deployable process from the EasyOrder backend —
EasyOrder consumes it purely as an MCP *client* over HTTP, exactly as it
would consume a real vendor-hosted MCP server: a URL plus a bearer token,
nothing shared in-process.

Run locally:
    MOCK_MCP_AUTH_TOKEN=dev-token python app/server.py
    # serves http://127.0.0.1:9100/mcp

Tool set mirrors the Swiggy MCP contract EasyOrder's agent depends on:
restaurant discovery/detail, food/instamart search, cart creation, and the
order lifecycle (place/history/current-status/delivery-tracking).
"""

from __future__ import annotations

import itertools
import os
import re
from typing import Any

import uvicorn
from mcp.server.fastmcp import FastMCP
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse

ORDER_STATUS_SEQUENCE: tuple[str, ...] = (
    "placed",
    "preparing",
    "out_for_delivery",
    "delivered",
)

RESTAURANTS: tuple[dict[str, Any], ...] = (
    {
        "id": "rest-biryani-house",
        "name": "Biryani House",
        "cuisines": ["Biryani", "Mughlai"],
        "rating": 4.3,
        "eta_minutes": 35,
    },
    {
        "id": "rest-roll-house",
        "name": "Roll House",
        "cuisines": ["Rolls", "North Indian"],
        "rating": 4.1,
        "eta_minutes": 25,
    },
    {
        "id": "rest-dosa-corner",
        "name": "Dosa Corner",
        "cuisines": ["South Indian"],
        "rating": 4.5,
        "eta_minutes": 30,
    },
    {
        "id": "rest-pizza-yard",
        "name": "Pizza Yard",
        "cuisines": ["Pizza", "Italian"],
        "rating": 4.0,
        "eta_minutes": 40,
    },
    {
        "id": "rest-moti-mahal",
        "name": "MotiMahal",
        "cuisines": ["North Indian", "Mughlai"],
        "rating": 4.4,
        "eta_minutes": 40,
    },
    {
        "id": "rest-spice-garden",
        "name": "Spice Garden",
        "cuisines": ["North Indian", "Tandoor"],
        "rating": 4.2,
        "eta_minutes": 30,
    },
    {
        "id": "rest-biryani-by-kilo",
        "name": "BiryaniByKilo",
        "cuisines": ["Biryani", "North Indian"],
        "rating": 4.2,
        "eta_minutes": 45,
    },
)

FOOD_ITEMS: tuple[dict[str, Any], ...] = (
    {
        "id": "food-chicken-biryani",
        "title": "Chicken dum biryani family pack",
        "price": "620.00",
        "diet": "non-veg",
        "restaurant": {"id": "rest-biryani-house", "name": "Biryani House"},
    },
    {
        "id": "food-paneer-roll",
        "title": "Paneer tikka rolls",
        "price": "180.00",
        "diet": "veg",
        "restaurant": {"id": "rest-roll-house", "name": "Roll House"},
    },
    {
        "id": "food-masala-dosa",
        "title": "Masala dosa",
        "price": "140.00",
        "diet": "veg",
        "restaurant": {"id": "rest-dosa-corner", "name": "Dosa Corner"},
    },
    {
        "id": "food-farmhouse-pizza",
        "title": "Large farmhouse pizza",
        "price": "560.00",
        "diet": "veg",
        "restaurant": {"id": "rest-pizza-yard", "name": "Pizza Yard"},
    },
    {
        "id": "food-mixed-veg",
        "title": "Mixed veg curry",
        "price": "240.00",
        "diet": "veg",
        "restaurant": {"id": "rest-spice-garden", "name": "Spice Garden"},
    },
    {
        "id": "food-tandoori-roti",
        "title": "Tandoori roti",
        "price": "45.00",
        "diet": "veg",
        "restaurant": {"id": "rest-spice-garden", "name": "Spice Garden"},
    },
    {
        "id": "food-mm-paneer-tikka",
        "title": "Paneer Tikka",
        "price": "260.00",
        "diet": "veg",
        "restaurant": {"id": "rest-moti-mahal", "name": "MotiMahal"},
    },
    {
        "id": "food-mm-chicken-65",
        "title": "Chicken 65",
        "price": "320.00",
        "diet": "non-veg",
        "restaurant": {"id": "rest-moti-mahal", "name": "MotiMahal"},
    },
    {
        "id": "food-mm-butter-naan",
        "title": "Butter Naan",
        "price": "60.00",
        "diet": "veg",
        "restaurant": {"id": "rest-moti-mahal", "name": "MotiMahal"},
    },
    {
        "id": "food-mm-dal-makhani",
        "title": "Dal Makhani",
        "price": "220.00",
        "diet": "veg",
        "restaurant": {"id": "rest-moti-mahal", "name": "MotiMahal"},
    },
    {
        "id": "food-bbk-egg-biryani",
        "title": "Egg Biryani",
        "price": "300.00",
        "diet": "non-veg",
        "restaurant": {"id": "rest-biryani-by-kilo", "name": "BiryaniByKilo"},
    },
    {
        "id": "food-bbk-chicken-biryani",
        "title": "Chicken Biryani",
        "price": "340.00",
        "diet": "non-veg",
        "restaurant": {"id": "rest-biryani-by-kilo", "name": "BiryaniByKilo"},
    },
    {
        "id": "food-bbk-veg-biryani",
        "title": "Veg Biryani",
        "price": "260.00",
        "diet": "veg",
        "restaurant": {"id": "rest-biryani-by-kilo", "name": "BiryaniByKilo"},
    },
)

INSTAMART_ITEMS: tuple[dict[str, Any], ...] = (
    {
        "sku": "im-cola",
        "name": "Cola 2L bottle",
        "price_rupees": "110",
        "brand": "Thums Up",
        "store": {"name": "Instamart Mock Store"},
    },
    {
        "sku": "im-icecream",
        "name": "Vanilla ice cream tub",
        "price_rupees": "220",
        "brand": "Cream Bell",
        "store": {"name": "Instamart Mock Store"},
    },
)

# Long-running server process => a plain in-memory store is legitimate here
# (unlike a per-call subprocess, state naturally survives across tool calls).
_order_seq = itertools.count(1)
_orders: dict[str, dict[str, Any]] = {}


def _advance_status(order: dict[str, Any]) -> str:
    poll_count = order.get("poll_count", 0)
    status = ORDER_STATUS_SEQUENCE[min(poll_count, len(ORDER_STATUS_SEQUENCE) - 1)]
    order["poll_count"] = poll_count + 1
    order["status"] = status
    return status


def _public_order(order: dict[str, Any]) -> dict[str, Any]:
    return {k: v for k, v in order.items() if k != "poll_count"}


mcp = FastMCP(name="mock-swiggy-mcp")


@mcp.tool()
def get_restaurants(lat: float, lng: float) -> dict[str, Any]:
    """Browse nearby restaurants without a search query."""
    del lat, lng
    return {"items": [dict(r) for r in RESTAURANTS]}


@mcp.tool()
def get_restaurant(restaurant_id: str) -> dict[str, Any]:
    """Return details for one restaurant."""
    for restaurant in RESTAURANTS:
        if restaurant["id"] == restaurant_id:
            return dict(restaurant)
    return {
        "id": restaurant_id,
        "name": f"Mock Restaurant {restaurant_id}",
        "cuisines": ["Multi-cuisine"],
        "rating": 4.0,
        "eta_minutes": 35,
    }


@mcp.tool()
def search_restaurants(lat: float, lng: float, query: str) -> dict[str, Any]:
    """Search Swiggy Food restaurants or dishes.

    Ranks by word overlap against the dish title and its restaurant name, so a
    multi-dish query ("chicken biryani mixed veg tandoori roti") answers for
    every dish it names in one call. This used to ignore the query entirely and
    return the whole catalogue in a fixed order, which made the caller's first
    result an accident of list position rather than of relevance.
    """
    del lat, lng
    wanted = _words(query)
    if not wanted:
        return {"items": [dict(item) for item in FOOD_ITEMS]}

    ranked: list[tuple[int, int, dict[str, Any]]] = []
    for position, item in enumerate(FOOD_ITEMS):
        haystack = _words(f"{item['title']} {item['restaurant']['name']}")
        score = len(wanted & haystack)
        if score:
            ranked.append((-score, position, dict(item)))
    if not ranked:
        # An unknown dish still gets the house list back; the caller decides
        # whether anything is close enough to seed.
        return {"items": [dict(item) for item in FOOD_ITEMS]}
    return {"items": [item for _score, _position, item in sorted(ranked, key=lambda row: row[:2])]}


def _words(text: str) -> set[str]:
    return {word for word in re.findall(r"[a-z]+", text.lower()) if len(word) > 2}


@mcp.tool()
def get_restaurant_menu(restaurant_id: str) -> dict[str, Any]:
    """Return a restaurant's menu."""
    items = [dict(item) for item in FOOD_ITEMS if item["restaurant"]["id"] == restaurant_id]
    if not items:
        items = [
            {
                "id": f"{restaurant_id}-combo",
                "title": "Family meal combo",
                "price": "720.00",
                "diet": "any",
                "restaurant": {"id": restaurant_id, "name": f"Mock Restaurant {restaurant_id}"},
            }
        ]
    return {"items": items}


@mcp.tool()
def search_instamart(lat: float, lng: float, query: str) -> dict[str, Any]:
    """Search Swiggy Instamart items."""
    del lat, lng, query
    return {"items": [dict(item) for item in INSTAMART_ITEMS]}


@mcp.tool()
def get_substitute_items(item_id: str) -> dict[str, Any]:
    """Return substitute candidates for an unavailable item."""
    del item_id
    return {"items": [dict(INSTAMART_ITEMS[0])]}


@mcp.tool()
def exchange_oauth_code(oauth_code: str) -> dict[str, Any]:
    """Exchange a Swiggy OAuth code for an access token."""
    if oauth_code == "mock-oauth-fail":
        return {"error": "mock oauth exchange failed"}
    return {"access_token": "mock-swiggy-server-token"}


@mcp.tool()
def create_cart(auth_header: str, vertical: str, items: list[dict[str, Any]]) -> dict[str, Any]:
    """Create a Swiggy checkout cart for one vertical (host-only checkout handoff)."""
    del items
    if not auth_header.startswith("Bearer "):
        return {"error": "missing Swiggy authorization"}
    return {
        "status": "created",
        "checkout_url": f"https://mock.swiggy.local/checkout/{vertical}/server",
    }


@mcp.tool()
def place_order(
    auth_header: str,
    vertical: str,
    restaurant_id: str | None,
    items: list[dict[str, Any]],
) -> dict[str, Any]:
    """Place a finalized order."""
    if not auth_header.startswith("Bearer "):
        return {"error": "missing Swiggy authorization"}
    order_id = f"order-{next(_order_seq)}"
    total = sum(float(item.get("price", 0)) for item in items)
    order = {
        "order_id": order_id,
        "customer_id": auth_header,
        "vertical": vertical,
        "restaurant_id": restaurant_id,
        "items": items,
        "total": f"{total:.2f}",
        "status": ORDER_STATUS_SEQUENCE[0],
        "poll_count": 0,
    }
    _orders[order_id] = order
    return _public_order(order)


@mcp.tool()
def get_order_history(auth_header: str) -> dict[str, Any]:
    """Return past orders for the authenticated customer, newest first."""
    matching = [order for order in _orders.values() if order["customer_id"] == auth_header]
    matching.reverse()
    return {"items": [_public_order(order) for order in matching]}


@mcp.tool()
def get_current_order(auth_header: str, order_id: str) -> dict[str, Any]:
    """Return the live status of one order."""
    order = _orders.get(order_id)
    if order is None or order["customer_id"] != auth_header:
        return {"error": f"{order_id} is not a known order"}
    status = _advance_status(order)
    return {**_public_order(order), "status": status}


@mcp.tool()
def get_delivery_update(order_id: str) -> dict[str, Any]:
    """Return delivery/rider tracking state for one order."""
    order = _orders.get(order_id)
    if order is None:
        return {"error": f"{order_id} is not a known order"}
    status = _advance_status(order)
    remaining_steps = max(0, len(ORDER_STATUS_SEQUENCE) - 1 - ORDER_STATUS_SEQUENCE.index(status))
    return {
        "order_id": order_id,
        "status": status,
        "eta_minutes": remaining_steps * 10,
        "rider_name": "Mock Rider" if status == "out_for_delivery" else None,
    }


class BearerAuthMiddleware(BaseHTTPMiddleware):
    """Rejects requests without the configured bearer token, when one is set."""

    def __init__(self, app: Any, token: str) -> None:
        super().__init__(app)
        self.token = token

    async def dispatch(self, request: Request, call_next: Any) -> Any:
        if self.token:
            expected = f"Bearer {self.token}"
            if request.headers.get("authorization") != expected:
                return JSONResponse({"error": "unauthorized"}, status_code=401)
        return await call_next(request)


def build_app() -> Any:
    app = mcp.streamable_http_app()
    token = os.environ.get("MOCK_MCP_AUTH_TOKEN", "")
    if token:
        app.add_middleware(BearerAuthMiddleware, token=token)
    return app


app = build_app()


if __name__ == "__main__":
    host = os.environ.get("MOCK_MCP_HOST", "127.0.0.1")
    port = int(os.environ.get("MOCK_MCP_PORT", "9100"))
    uvicorn.run(app, host=host, port=port)
