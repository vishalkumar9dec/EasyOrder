import asyncio
from decimal import Decimal

import pytest

from app.models.session import Vertical
from app.services.mock_swiggy import (
    MockSwiggyItemUnavailableError,
    MockSwiggyMcpClient,
    MockSwiggyScenario,
)
from app.services.protocols import ISwiggyMcpClient


def run(coro):
    return asyncio.run(coro)


def test_mock_swiggy_client_conforms_to_protocol_shape() -> None:
    client: ISwiggyMcpClient = MockSwiggyMcpClient()

    food = run(client.search_restaurants(12.9, 77.5, "biryani"))
    instamart = run(client.search_instamart(12.9, 77.5, "drinks"))

    assert food[0]["vertical"] == Vertical.FOOD
    assert food[0]["restaurant_id"]
    assert food[0]["restaurant_name"]
    assert instamart[0]["vertical"] == Vertical.INSTAMART
    assert instamart[0]["brand_name"]
    assert instamart[0]["source_label"]


def test_mock_swiggy_scenarios_cover_empty_and_substitute_behavior() -> None:
    client = MockSwiggyMcpClient(MockSwiggyScenario(name="empty", empty_food=True))

    assert run(client.search_restaurants(12.9, 77.5, "biryani")) == []
    substitute = run(client.get_substitute_items("im-icecream"))[0]

    assert substitute["name"] == "Butterscotch ice cream tub"


def test_mock_swiggy_checkout_reports_unavailable_and_price_change_items() -> None:
    unavailable = MockSwiggyMcpClient(
        MockSwiggyScenario(name="stock", unavailable_item_id="im-icecream")
    )

    with pytest.raises(MockSwiggyItemUnavailableError):
        run(
            unavailable.create_cart(
                "Bearer test",
                "instamart",
                [{"item_id": "im-icecream", "price": "220.00"}],
            )
        )

    price_change = MockSwiggyMcpClient(
        MockSwiggyScenario(name="price", price_change_item_id="food-sushi")
    )
    result = run(
        price_change.create_cart(
            "Bearer test",
            "food",
            [{"item_id": "food-sushi", "price": "1850.00"}],
        )
    )

    assert result["status"] == "price_changed"
    assert Decimal(result["new_price"]) == Decimal("1875.00")
