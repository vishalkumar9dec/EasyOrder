import asyncio

import pytest

from app.models.session import DietaryTag, Vertical
from app.services.mock_swiggy import MockSwiggyMcpClient
from app.services.swiggy_mcp import (
    SwiggyMcpClient,
    SwiggyMcpConfigurationError,
    SwiggyMcpToolError,
    create_swiggy_client,
    normalize_food_item,
    normalize_instamart_item,
    parse_server_env,
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
        create_swiggy_client(mode="mock", server_path="", server_env="{}"),
        MockSwiggyMcpClient,
    )
    with pytest.raises(SwiggyMcpConfigurationError):
        create_swiggy_client(mode="mcp", server_path="", server_env="{}")


def test_parse_server_env_requires_json_object() -> None:
    assert parse_server_env('{"SWIGGY_ENV":"sandbox"}') == {"SWIGGY_ENV": "sandbox"}
    with pytest.raises(SwiggyMcpConfigurationError):
        parse_server_env("[]")
