import asyncio
from decimal import Decimal

import pytest

from app.models.session import Vertical
from app.services.mock_swiggy import (
    MockSwiggyItemUnavailableError,
    MockSwiggyMcpClient,
    MockSwiggyOAuthError,
    MockSwiggyOrderNotFoundError,
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


def test_mock_swiggy_get_restaurants_and_get_restaurant() -> None:
    client = MockSwiggyMcpClient()

    restaurants = run(client.get_restaurants(12.9, 77.5))
    assert len(restaurants) >= 1
    assert {"restaurant_id", "name", "cuisines", "rating", "eta_minutes"} <= restaurants[0].keys()

    known = run(client.get_restaurant(restaurants[0]["restaurant_id"]))
    assert known["restaurant_id"] == restaurants[0]["restaurant_id"]

    unknown = run(client.get_restaurant("rest-does-not-exist"))
    assert unknown["restaurant_id"] == "rest-does-not-exist"


def test_mock_swiggy_place_order_and_order_history() -> None:
    client = MockSwiggyMcpClient()
    auth = "Bearer test-customer"

    order = run(
        client.place_order(
            auth,
            "food",
            "rest-biryani-house",
            [{"item_id": "food-chicken-biryani", "price": "620.00"}],
        )
    )

    assert order["order_id"]
    assert order["status"] == "placed"
    assert Decimal(order["total"]) == Decimal("620.00")

    history = run(client.get_order_history(auth))
    assert history[0]["order_id"] == order["order_id"]

    other_customer_history = run(client.get_order_history("Bearer someone-else"))
    assert other_customer_history == []

    with pytest.raises(MockSwiggyOAuthError):
        run(client.place_order("missing-bearer-prefix", "food", "rest-1", []))


def test_mock_swiggy_order_status_progresses_deterministically_on_poll() -> None:
    client = MockSwiggyMcpClient()
    auth = "Bearer test-customer"
    order = run(client.place_order(auth, "food", "rest-biryani-house", []))
    order_id = order["order_id"]

    statuses = [run(client.get_current_order(auth, order_id))["status"] for _ in range(5)]

    assert statuses == ["placed", "preparing", "out_for_delivery", "delivered", "delivered"]

    with pytest.raises(MockSwiggyOrderNotFoundError):
        run(client.get_current_order(auth, "order-unknown"))
    with pytest.raises(MockSwiggyOrderNotFoundError):
        run(client.get_current_order("Bearer wrong-customer", order_id))


def test_mock_swiggy_delivery_update_reports_rider_only_when_out_for_delivery() -> None:
    client = MockSwiggyMcpClient()
    auth = "Bearer test-customer"
    order = run(client.place_order(auth, "food", "rest-biryani-house", []))
    order_id = order["order_id"]

    first = run(client.get_delivery_update(order_id))
    second = run(client.get_delivery_update(order_id))
    third = run(client.get_delivery_update(order_id))

    assert first["status"] == "placed"
    assert first["rider_name"] is None
    assert second["status"] == "preparing"
    assert second["rider_name"] is None
    assert third["status"] == "out_for_delivery"
    assert third["rider_name"] == "Mock Rider"

    with pytest.raises(MockSwiggyOrderNotFoundError):
        run(client.get_delivery_update("order-unknown"))
