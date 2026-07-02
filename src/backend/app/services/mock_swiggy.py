"""Deterministic Swiggy MCP client for local development and tests."""

from __future__ import annotations

import asyncio
from dataclasses import dataclass
from decimal import Decimal
from typing import Any

from app.models.session import DietaryTag, Vertical


class MockSwiggyTimeoutError(TimeoutError):
    """Raised when a mock scenario is configured to exceed worker timeouts."""


class MockSwiggyItemUnavailableError(RuntimeError):
    """Raised when a mock checkout item is unavailable."""


class MockSwiggyOAuthError(RuntimeError):
    """Raised when mock OAuth exchange fails."""


class MockSwiggyCartCreationError(RuntimeError):
    """Raised when mock cart creation fails after OAuth."""


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
        return [
            self._food_item(
                f"{restaurant_id}-combo",
                "Family meal combo",
                "720.00",
                DietaryTag.ANY,
                restaurant_id=restaurant_id,
                restaurant_name=f"Mock Restaurant {restaurant_id}",
            ),
        ]

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
