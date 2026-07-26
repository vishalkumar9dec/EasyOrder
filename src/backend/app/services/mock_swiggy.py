"""Deterministic Swiggy MCP client for local development and tests."""

from __future__ import annotations

import asyncio
import itertools
from collections.abc import Sequence
from dataclasses import dataclass
from decimal import Decimal
from typing import Any

from app.models.session import DietaryTag, Vertical
from app.services import menu_matching

# Order lifecycle a mock order walks through on successive status polls.
# Deterministic (call-count driven, not wall-clock) so tests never race.
ORDER_STATUS_SEQUENCE: tuple[str, ...] = (
    "placed",
    "preparing",
    "out_for_delivery",
    "delivered",
)

# Static restaurant directory shared by get_restaurants/get_restaurant so IDs
# stay consistent with the ones search_restaurants already returns.
MOCK_RESTAURANTS: tuple[dict[str, Any], ...] = (
    {
        "restaurant_id": "rest-biryani-house",
        "name": "Biryani House",
        "cuisines": ["Biryani", "Mughlai"],
        "rating": 4.3,
        "eta_minutes": 35,
    },
    {
        "restaurant_id": "rest-roll-house",
        "name": "Roll House",
        "cuisines": ["Rolls", "North Indian"],
        "rating": 4.1,
        "eta_minutes": 25,
    },
    {
        "restaurant_id": "rest-dosa-corner",
        "name": "Dosa Corner",
        "cuisines": ["South Indian"],
        "rating": 4.5,
        "eta_minutes": 30,
    },
    {
        "restaurant_id": "rest-pizza-yard",
        "name": "Pizza Yard",
        "cuisines": ["Pizza", "Italian"],
        "rating": 4.0,
        "eta_minutes": 40,
    },
    {
        "restaurant_id": "rest-moti-mahal",
        "name": "MotiMahal",
        "cuisines": ["North Indian", "Mughlai"],
        "rating": 4.4,
        "eta_minutes": 40,
    },
    {
        "restaurant_id": "rest-biryani-by-kilo",
        "name": "BiryaniByKilo",
        "cuisines": ["Biryani", "North Indian"],
        "rating": 4.2,
        "eta_minutes": 45,
    },
)


# Real multi-dish catalogs, keyed by restaurant_id. get_restaurant_menu falls
# back to a synthetic single-item combo for any restaurant not listed here
# (the original 4 restaurants and any unknown id), preserving prior behavior.
MOCK_MENUS: dict[str, tuple[dict[str, Any], ...]] = {
    "rest-moti-mahal": (
        {
            "item_id": "food-mm-paneer-tikka",
            "name": "Paneer Tikka",
            "price": "260.00",
            "dietary_tag": DietaryTag.VEG,
        },
        {
            "item_id": "food-mm-chicken-65",
            "name": "Chicken 65",
            "price": "320.00",
            "dietary_tag": DietaryTag.NON_VEG,
        },
        {
            "item_id": "food-mm-butter-naan",
            "name": "Butter Naan",
            "price": "60.00",
            "dietary_tag": DietaryTag.VEG,
        },
        {
            "item_id": "food-mm-dal-makhani",
            "name": "Dal Makhani",
            "price": "220.00",
            "dietary_tag": DietaryTag.VEG,
        },
    ),
    "rest-biryani-by-kilo": (
        {
            "item_id": "food-bbk-egg-biryani",
            "name": "Egg Biryani",
            "price": "300.00",
            "dietary_tag": DietaryTag.NON_VEG,
        },
        {
            "item_id": "food-bbk-chicken-biryani",
            "name": "Chicken Biryani",
            "price": "340.00",
            "dietary_tag": DietaryTag.NON_VEG,
        },
        {
            "item_id": "food-bbk-veg-biryani",
            "name": "Veg Biryani",
            "price": "260.00",
            "dietary_tag": DietaryTag.VEG,
        },
    ),
}


class MockSwiggyTimeoutError(TimeoutError):
    """Raised when a mock scenario is configured to exceed worker timeouts."""


class MockSwiggyItemUnavailableError(RuntimeError):
    """Raised when a mock checkout item is unavailable."""


class MockSwiggyOAuthError(RuntimeError):
    """Raised when mock OAuth exchange fails."""


class MockSwiggyCartCreationError(RuntimeError):
    """Raised when mock cart creation fails after OAuth."""


class MockSwiggyOrderNotFoundError(RuntimeError):
    """Raised when an order_id is not known to this mock client instance."""


@dataclass(frozen=True)
class MockSwiggyScenario:
    """Configures deterministic mock client behavior."""

    name: str = "normal"
    food_latency_seconds: float = 0
    instamart_latency_seconds: float = 0
    empty_food: bool = False
    empty_instamart: bool = False
    unavailable_item_id: str | None = None
    price_change_item_id: str | None = None
    oauth_failure: bool = False
    cart_failure_vertical: str | None = None


class MockSwiggyMcpClient:
    """Protocol-compatible Swiggy client with deterministic local responses."""

    def __init__(self, scenario: MockSwiggyScenario | None = None) -> None:
        self.scenario = scenario or MockSwiggyScenario()
        self._order_seq = itertools.count(1)
        # order_id -> order record (customer_id, items, status polls, etc.)
        self._orders: dict[str, dict[str, Any]] = {}
        # order_id -> number of times get_current_order/get_delivery_update
        # has been polled; drives the deterministic status progression.
        self._order_polls: dict[str, int] = {}

    async def search_restaurants(
        self,
        lat: float,
        lng: float,
        query: str,
    ) -> list[dict[str, Any]]:
        del lat, lng
        await self._sleep_or_timeout(self.scenario.food_latency_seconds)
        if self.scenario.empty_food:
            return []

        query_lower = query.lower()
        if "veg" in query_lower or "paneer" in query_lower:
            return [
                self._food_item(
                    "food-paneer-roll",
                    "Paneer tikka rolls",
                    "180.00",
                    DietaryTag.VEG,
                    restaurant_id="rest-roll-house",
                    restaurant_name="Roll House",
                ),
                self._food_item(
                    "food-masala-dosa",
                    "Masala dosa",
                    "140.00",
                    DietaryTag.VEG,
                    restaurant_id="rest-dosa-corner",
                    restaurant_name="Dosa Corner",
                ),
            ]
        if "pizza" in query_lower:
            return [
                self._food_item(
                    "food-farmhouse-pizza",
                    "Large farmhouse pizza",
                    "560.00",
                    DietaryTag.VEG,
                    restaurant_id="rest-pizza-yard",
                    restaurant_name="Pizza Yard",
                ),
                self._food_item(
                    "food-brownie-box",
                    "Chocolate brownie box",
                    "320.00",
                    DietaryTag.VEG,
                    restaurant_id="rest-pizza-yard",
                    restaurant_name="Pizza Yard",
                ),
            ]
        return [
            self._food_item(
                "food-chicken-biryani",
                "Chicken dum biryani family pack",
                "620.00",
                DietaryTag.NON_VEG,
                restaurant_id="rest-biryani-house",
                restaurant_name="Biryani House",
            ),
            self._food_item(
                "food-paneer-roll",
                "Paneer tikka rolls",
                "180.00",
                DietaryTag.VEG,
                restaurant_id="rest-roll-house",
                restaurant_name="Roll House",
            ),
        ]

    async def get_restaurant_menu(self, restaurant_id: str) -> list[dict[str, Any]]:
        menu = MOCK_MENUS.get(restaurant_id)
        if menu is not None:
            restaurant_name = self._restaurant_name(restaurant_id)
            items = [
                self._food_item(
                    dish["item_id"],
                    dish["name"],
                    dish["price"],
                    dish["dietary_tag"],
                    restaurant_id=restaurant_id,
                    restaurant_name=restaurant_name,
                )
                for dish in menu
            ]
        else:
            items = [
                self._food_item(
                    f"{restaurant_id}-combo",
                    "Family meal combo",
                    "720.00",
                    DietaryTag.ANY,
                    restaurant_id=restaurant_id,
                    restaurant_name=f"Mock Restaurant {restaurant_id}",
                ),
            ]
        return self._apply_menu_scenario(items)

    def _apply_menu_scenario(self, items: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """Simulates a menu changing between when it was first read and a
        later re-check — reuses the same scenario fields create_cart already
        uses for its own price-changed/unavailable-item simulation."""
        if self.scenario.unavailable_item_id is not None:
            items = [item for item in items if item["item_id"] != self.scenario.unavailable_item_id]
        if self.scenario.price_change_item_id is not None:
            items = [
                {**item, "price": str(Decimal(str(item["price"])) + Decimal("25.00"))}
                if item["item_id"] == self.scenario.price_change_item_id
                else item
                for item in items
            ]
        return items

    @staticmethod
    def _restaurant_name(restaurant_id: str) -> str:
        for restaurant in MOCK_RESTAURANTS:
            if restaurant["restaurant_id"] == restaurant_id:
                return str(restaurant["name"])
        return f"Mock Restaurant {restaurant_id}"

    async def search_instamart(
        self,
        lat: float,
        lng: float,
        query: str,
    ) -> list[dict[str, Any]]:
        del lat, lng
        await self._sleep_or_timeout(self.scenario.instamart_latency_seconds)
        if self.scenario.empty_instamart:
            return []

        query_lower = query.lower()
        if "ice" in query_lower or "dessert" in query_lower:
            return [
                self._instamart_item(
                    "im-icecream",
                    "Vanilla ice cream tub",
                    "220.00",
                    brand_name="Cream Bell",
                ),
                self._instamart_item(
                    "im-spoons",
                    "Disposable dessert spoons",
                    "80.00",
                    brand_name="PartyPro",
                ),
            ]
        if "plate" in query_lower:
            return [
                self._instamart_item(
                    "im-plates",
                    "Disposable plates pack",
                    "140.00",
                    brand_name="PartyPro",
                ),
                self._instamart_item(
                    "im-napkins",
                    "Party napkins",
                    "90.00",
                    brand_name="SoftFold",
                ),
            ]
        return [
            self._instamart_item("im-cola", "Cola 2L bottle", "110.00", brand_name="Thums Up"),
            self._instamart_item(
                "im-water",
                "Sparkling water cans",
                "180.00",
                brand_name="Kinley",
            ),
        ]

    async def exchange_oauth_code(self, oauth_code: str) -> str:
        if self.scenario.oauth_failure or oauth_code == "mock-oauth-fail":
            raise MockSwiggyOAuthError("Mock OAuth exchange failed")
        return f"Bearer mock-swiggy-token-{self.scenario.name}"

    async def create_cart(
        self,
        auth_header: str,
        vertical: str,
        items: list[dict[str, Any]],
    ) -> dict[str, Any]:
        if not auth_header.startswith("Bearer "):
            raise MockSwiggyOAuthError("Missing Swiggy authorization")
        if self.scenario.cart_failure_vertical == vertical:
            raise MockSwiggyCartCreationError(f"{vertical} cart creation failed")
        for item in items:
            if item.get("item_id") == self.scenario.unavailable_item_id:
                raise MockSwiggyItemUnavailableError(f"{item['item_id']} is unavailable")
            if item.get("item_id") == self.scenario.price_change_item_id:
                changed_price = Decimal(str(item["price"])) + Decimal("25.00")
                return {
                    "status": "price_changed",
                    "vertical": vertical,
                    "item_id": item["item_id"],
                    "new_price": str(changed_price),
                }

        return {
            "status": "created",
            "vertical": vertical,
            "checkout_url": self._checkout_url(vertical, items),
        }

    def _checkout_url(self, vertical: str, items: list[dict[str, Any]]) -> str:
        if vertical == Vertical.FOOD:
            source = items[0].get("restaurant_id") or "restaurant"
        else:
            source = "instamart"
        return f"https://mock.swiggy.local/checkout/{vertical}/{source}/{self.scenario.name}"

    async def get_substitute_items(self, item_id: str) -> list[dict[str, Any]]:
        if item_id == "im-icecream":
            return [
                self._instamart_item(
                    "im-butterscotch",
                    "Butterscotch ice cream tub",
                    "230.00",
                    brand_name="Cream Bell",
                )
            ]
        return [
            self._instamart_item(
                "im-substitute",
                "Suggested substitute item",
                "120.00",
                brand_name="Mock Brand",
            )
        ]

    async def find_restaurant_by_name(self, name: str) -> dict[str, Any] | None:
        return menu_matching.find_restaurant_by_name(MOCK_RESTAURANTS, name)

    async def match_menu_items(
        self,
        restaurant_id: str,
        dish_names: Sequence[str],
    ) -> list[dict[str, Any]]:
        menu = await self.get_restaurant_menu(restaurant_id)
        return menu_matching.match_menu_items(menu, dish_names)

    async def get_restaurants(self, lat: float, lng: float) -> list[dict[str, Any]]:
        del lat, lng
        return [dict(restaurant) for restaurant in MOCK_RESTAURANTS]

    async def get_restaurant(self, restaurant_id: str) -> dict[str, Any]:
        for restaurant in MOCK_RESTAURANTS:
            if restaurant["restaurant_id"] == restaurant_id:
                return dict(restaurant)
        # Unknown IDs still resolve, mirroring get_restaurant_menu's synthesis
        # behavior so a restaurant seen only via search/menu can be looked up.
        return {
            "restaurant_id": restaurant_id,
            "name": f"Mock Restaurant {restaurant_id}",
            "cuisines": ["Multi-cuisine"],
            "rating": 4.0,
            "eta_minutes": 35,
        }

    async def place_order(
        self,
        auth_header: str,
        vertical: str,
        restaurant_id: str,
        items: list[dict[str, Any]],
    ) -> dict[str, Any]:
        if not auth_header.startswith("Bearer "):
            raise MockSwiggyOAuthError("Missing Swiggy authorization")
        order_id = f"order-{next(self._order_seq)}"
        total = sum((Decimal(str(item["price"])) for item in items), Decimal("0.00"))
        order = {
            "order_id": order_id,
            "customer_id": auth_header,
            "vertical": vertical,
            "restaurant_id": restaurant_id,
            "items": list(items),
            "total": str(total.quantize(Decimal("0.01"))),
            "status": ORDER_STATUS_SEQUENCE[0],
        }
        self._orders[order_id] = order
        self._order_polls[order_id] = 0
        return dict(order)

    async def get_order_history(self, auth_header: str) -> list[dict[str, Any]]:
        orders = [order for order in self._orders.values() if order["customer_id"] == auth_header]
        return [dict(order) for order in reversed(orders)]

    async def get_current_order(self, auth_header: str, order_id: str) -> dict[str, Any]:
        order = self._orders.get(order_id)
        if order is None or order["customer_id"] != auth_header:
            raise MockSwiggyOrderNotFoundError(f"{order_id} is not a known order")
        status = self._advance_status(order_id)
        return {**order, "status": status}

    async def get_delivery_update(self, order_id: str) -> dict[str, Any]:
        if order_id not in self._orders:
            raise MockSwiggyOrderNotFoundError(f"{order_id} is not a known order")
        status = self._advance_status(order_id)
        remaining_steps = max(
            0, len(ORDER_STATUS_SEQUENCE) - 1 - ORDER_STATUS_SEQUENCE.index(status)
        )
        return {
            "order_id": order_id,
            "status": status,
            "eta_minutes": remaining_steps * 10,
            "rider_name": "Mock Rider" if status == "out_for_delivery" else None,
        }

    def _advance_status(self, order_id: str) -> str:
        poll_count = self._order_polls.get(order_id, 0)
        status = ORDER_STATUS_SEQUENCE[min(poll_count, len(ORDER_STATUS_SEQUENCE) - 1)]
        self._order_polls[order_id] = poll_count + 1
        self._orders[order_id]["status"] = status
        return status

    async def _sleep_or_timeout(self, latency_seconds: float) -> None:
        if latency_seconds <= 0:
            return
        await asyncio.sleep(latency_seconds)

    @staticmethod
    def _food_item(
        item_id: str,
        name: str,
        price: str,
        dietary_tag: DietaryTag,
        restaurant_id: str,
        restaurant_name: str,
    ) -> dict[str, Any]:
        return {
            "item_id": item_id,
            "name": name,
            "price": price,
            "dietary_tag": dietary_tag,
            "vertical": Vertical.FOOD,
            "source": "mock_swiggy",
            "restaurant_id": restaurant_id,
            "restaurant_name": restaurant_name,
        }

    @staticmethod
    def _instamart_item(
        item_id: str,
        name: str,
        price: str,
        brand_name: str,
        source_label: str = "Instamart Mock Store",
    ) -> dict[str, Any]:
        return {
            "item_id": item_id,
            "name": name,
            "price": price,
            "dietary_tag": DietaryTag.VEG,
            "vertical": Vertical.INSTAMART,
            "source": "mock_swiggy",
            "brand_name": brand_name,
            "source_label": source_label,
        }
