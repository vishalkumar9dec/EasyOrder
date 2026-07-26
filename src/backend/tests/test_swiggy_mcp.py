import asyncio

import pytest

from app.models.session import DietaryTag, Vertical
from app.services.mock_swiggy import MockSwiggyMcpClient
from app.services.swiggy_mcp import (
    HttpMCPToolRunner,
    SwiggyMcpClient,
    SwiggyMcpConfigurationError,
    SwiggyMcpToolError,
    create_swiggy_client,
    normalize_food_item,
    normalize_instamart_item,
    normalize_order,
    normalize_restaurant,
)


def run(coro):
    return asyncio.run(coro)


class FakeRunner:
    def __init__(self, responses: dict[str, dict]) -> None:
        self.responses = responses
        self.calls: list[tuple[str, dict]] = []

    async def call_tool(self, tool_name: str, arguments: dict) -> dict:
        self.calls.append((tool_name, arguments))
        return self.responses[tool_name]


def test_swiggy_mcp_normalizes_food_and_instamart_source_attribution() -> None:
    food = normalize_food_item(
        {
            "id": "dish-1",
            "title": "Paneer rolls",
            "price": 180,
            "diet": "veg",
            "restaurant": {"id": "rest-roll-house", "name": "Roll House"},
        }
    )
    instamart = normalize_instamart_item(
        {
            "sku": "im-cola",
            "name": "Cola 2L bottle",
            "price_rupees": "110",
            "brand": "Thums Up",
            "store": {"name": "Instamart Koramangala"},
        }
    )

    assert food == {
        "item_id": "dish-1",
        "name": "Paneer rolls",
        "price": "180.00",
        "dietary_tag": DietaryTag.VEG,
        "vertical": Vertical.FOOD,
        "source": "swiggy_mcp",
        "restaurant_id": "rest-roll-house",
        "restaurant_name": "Roll House",
    }
    assert instamart["brand_name"] == "Thums Up"
    assert instamart["source_label"] == "Instamart Koramangala"
    assert instamart["vertical"] == Vertical.INSTAMART


def test_swiggy_mcp_rejects_missing_source_attribution() -> None:
    with pytest.raises(SwiggyMcpToolError):
        normalize_food_item({"id": "dish-1", "name": "Paneer rolls", "price": 180})

    with pytest.raises(SwiggyMcpToolError):
        normalize_instamart_item({"id": "im-cola", "name": "Cola", "price": 110})


def test_swiggy_mcp_client_invokes_tools_and_maps_responses() -> None:
    runner = FakeRunner(
        {
            "search_restaurants": {
                "result": {
                    "items": [
                        {
                            "id": "food-biryani",
                            "name": "Chicken biryani",
                            "price": "620.00",
                            "dietary_tag": "NON-VEG",
                            "restaurant_id": "rest-biryani-house",
                            "restaurant_name": "Biryani House",
                        }
                    ]
                }
            },
            "exchange_oauth_code": {"access_token": "token-123"},
            "create_cart": {"status": "created", "checkout_url": "https://checkout.test/1"},
        }
    )
    client = SwiggyMcpClient(runner)

    food = run(client.search_restaurants(12.9, 77.5, "biryani"))
    auth_header = run(client.exchange_oauth_code("oauth-code"))
    cart = run(client.create_cart(auth_header, "food", [{"item_id": "food-biryani"}]))

    assert food[0]["restaurant_name"] == "Biryani House"
    assert auth_header == "Bearer token-123"
    assert cart["checkout_url"] == "https://checkout.test/1"
    assert [call[0] for call in runner.calls] == [
        "search_restaurants",
        "exchange_oauth_code",
        "create_cart",
    ]


def test_swiggy_mcp_client_maps_tool_errors() -> None:
    client = SwiggyMcpClient(FakeRunner({"search_instamart": {"error": "boom"}}))

    with pytest.raises(SwiggyMcpToolError):
        run(client.search_instamart(12.9, 77.5, "drinks"))


def test_swiggy_client_factory_keeps_mock_default_and_validates_mcp_config() -> None:
    assert isinstance(
        create_swiggy_client(mode="mock", server_url=""),
        MockSwiggyMcpClient,
    )
    with pytest.raises(SwiggyMcpConfigurationError):
        create_swiggy_client(mode="mcp", server_url="")

    real_client = create_swiggy_client(mode="mcp", server_url="http://localhost:9100/mcp")
    assert isinstance(real_client, SwiggyMcpClient)
    assert isinstance(real_client.runner, HttpMCPToolRunner)


def test_http_mcp_tool_runner_requires_server_url() -> None:
    with pytest.raises(SwiggyMcpConfigurationError):
        run(HttpMCPToolRunner(server_url="").call_tool("get_restaurants", {}))


def test_normalize_restaurant_and_order() -> None:
    restaurant = normalize_restaurant(
        {
            "id": "rest-1",
            "name": "Test Kitchen",
            "cuisines": ["Indian"],
            "rating": 4.2,
            "eta_minutes": 30,
        }
    )
    assert restaurant == {
        "restaurant_id": "rest-1",
        "name": "Test Kitchen",
        "cuisines": ["Indian"],
        "rating": 4.2,
        "eta_minutes": 30,
    }

    order = normalize_order(
        {
            "order_id": "order-1",
            "vertical": "food",
            "restaurant_id": "rest-1",
            "items": [{"item_id": "food-1", "price": "100.00"}],
            "total": "100.00",
            "status": "placed",
        }
    )
    assert order["order_id"] == "order-1"
    assert order["status"] == "placed"
    assert order["total"] == "100.00"


def test_swiggy_mcp_client_order_lifecycle_tools() -> None:
    runner = FakeRunner(
        {
            "get_restaurants": {
                "items": [
                    {
                        "id": "rest-1",
                        "name": "Test Kitchen",
                        "cuisines": [],
                        "rating": 4.0,
                        "eta_minutes": 20,
                    }
                ]
            },
            "get_restaurant": {
                "id": "rest-1",
                "name": "Test Kitchen",
                "cuisines": [],
                "rating": 4.0,
                "eta_minutes": 20,
            },
            "place_order": {
                "order_id": "order-1",
                "vertical": "food",
                "restaurant_id": "rest-1",
                "items": [],
                "total": "100.00",
                "status": "placed",
            },
            "get_order_history": {
                "items": [
                    {
                        "order_id": "order-1",
                        "vertical": "food",
                        "restaurant_id": "rest-1",
                        "items": [],
                        "total": "100.00",
                        "status": "delivered",
                    }
                ]
            },
            "get_current_order": {
                "order_id": "order-1",
                "vertical": "food",
                "restaurant_id": "rest-1",
                "items": [],
                "total": "100.00",
                "status": "preparing",
            },
            "get_delivery_update": {
                "order_id": "order-1",
                "status": "out_for_delivery",
                "eta_minutes": 10,
                "rider_name": "Mock Rider",
            },
        }
    )
    client = SwiggyMcpClient(runner)

    restaurants = run(client.get_restaurants(12.9, 77.5))
    restaurant = run(client.get_restaurant("rest-1"))
    order = run(client.place_order("Bearer token", "food", "rest-1", []))
    history = run(client.get_order_history("Bearer token"))
    current = run(client.get_current_order("Bearer token", "order-1"))
    delivery = run(client.get_delivery_update("order-1"))

    assert restaurants[0]["restaurant_id"] == "rest-1"
    assert restaurant["name"] == "Test Kitchen"
    assert order["order_id"] == "order-1"
    assert history[0]["status"] == "delivered"
    assert current["status"] == "preparing"
    assert delivery["rider_name"] == "Mock Rider"
    assert [call[0] for call in runner.calls] == [
        "get_restaurants",
        "get_restaurant",
        "place_order",
        "get_order_history",
        "get_current_order",
        "get_delivery_update",
    ]


def test_swiggy_mcp_client_resolves_restaurant_by_name_and_matches_menu_items() -> None:
    runner = FakeRunner(
        {
            "get_restaurants": {
                "items": [
                    {
                        "id": "rest-moti-mahal",
                        "name": "MotiMahal",
                        "cuisines": ["North Indian"],
                        "rating": 4.4,
                        "eta_minutes": 40,
                    }
                ]
            },
            "get_restaurant_menu": {
                "items": [
                    {
                        "id": "food-mm-paneer-tikka",
                        "name": "Paneer Tikka",
                        "price": "260.00",
                        "dietary_tag": "VEG",
                        "restaurant_id": "rest-moti-mahal",
                        "restaurant_name": "MotiMahal",
                    },
                    {
                        "id": "food-mm-chicken-65",
                        "name": "Chicken 65",
                        "price": "320.00",
                        "dietary_tag": "NON-VEG",
                        "restaurant_id": "rest-moti-mahal",
                        "restaurant_name": "MotiMahal",
                    },
                ]
            },
        }
    )
    client = SwiggyMcpClient(runner)

    restaurant = run(client.find_restaurant_by_name("motimahal"))
    assert restaurant is not None
    assert restaurant["restaurant_id"] == "rest-moti-mahal"

    missing = run(client.find_restaurant_by_name("does not exist"))
    assert missing is None

    matched = run(client.match_menu_items("rest-moti-mahal", ["paneer tikka", "missing dish"]))
    assert [item["name"] for item in matched] == ["Paneer Tikka"]
