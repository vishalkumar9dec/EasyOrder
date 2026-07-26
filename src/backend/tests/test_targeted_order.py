import asyncio
from datetime import timedelta

import pytest

from app.models.order import OrderStatus
from app.models.whatsapp import IncomingMessage
from app.services.agent import MockTargetedOrderIntentParser
from app.services.memory_db import InMemoryDBAdapter
from app.services.mock_swiggy import MockSwiggyMcpClient
from app.services.targeted_order import TargetedOrderService


def run(coro):
    return asyncio.run(coro)


def message(text: str, message_id: str = "wamid.targeted.1", sender_id: str = "919988776655"):
    return IncomingMessage(
        sender_id=sender_id,
        message_id=message_id,
        message_text=text,
        phone_number_id="business-42",
        timestamp="1782489000",
        is_easyorder_tagged=False,
    )


def service() -> TargetedOrderService:
    return TargetedOrderService(
        db=InMemoryDBAdapter(),
        swiggy_client=MockSwiggyMcpClient(),
        parser=MockTargetedOrderIntentParser(),
    )


def test_mock_parser_extracts_budget_gated_prompt() -> None:
    parsed = run(
        MockTargetedOrderIntentParser().parse(
            "Order paneer tikka and chicken 65 from MotiMahal restaurant and if the budget "
            "exceeds INR 800, let me know before placing the order"
        )
    )

    assert parsed is not None
    assert parsed.restaurant_name == "MotiMahal"
    assert parsed.dish_names == ["paneer tikka", "chicken 65"]
    assert parsed.budget_limit == 800
    assert parsed.delivery_deadline_minutes is None


def test_mock_parser_extracts_scheduled_delivery_prompt() -> None:
    parsed = run(
        MockTargetedOrderIntentParser().parse(
            "Order Egg Biryani for me from BiryaniByKilo and it should reach by 8PM"
        )
    )

    assert parsed is not None
    assert parsed.restaurant_name == "BiryaniByKilo"
    assert parsed.dish_names == ["Egg Biryani"]
    assert parsed.budget_limit is None
    assert parsed.delivery_deadline_minutes == 20 * 60


def test_mock_parser_returns_none_without_a_named_restaurant() -> None:
    assert run(MockTargetedOrderIntentParser().parse("get biryani for 4 under 2000")) is None


def test_under_budget_order_places_immediately() -> None:
    svc = service()

    reply = run(
        svc.handle_targeted_order_message(
            message("Order paneer tikka from MotiMahal restaurant")
        )
    )

    assert "Placed!" in reply
    orders = run(svc.db.list_orders_for_host("919988776655"))
    assert len(orders) == 1
    assert orders[0].status == OrderStatus.PLACED
    assert orders[0].swiggy_order_id is not None


def test_over_budget_order_creates_pending_confirmation_not_placed() -> None:
    svc = service()

    reply = run(
        svc.handle_targeted_order_message(
            message(
                "Order paneer tikka and chicken 65 from MotiMahal restaurant and if the "
                "budget exceeds INR 400, let me know before placing the order"
            )
        )
    )

    assert "exceeds your INR 400 budget" in reply
    orders = run(svc.db.list_orders_for_host("919988776655"))
    assert len(orders) == 1
    assert orders[0].status == OrderStatus.PENDING_CONFIRMATION
    assert orders[0].swiggy_order_id is None


def test_delivery_deadline_order_is_scheduled_not_placed() -> None:
    svc = service()

    reply = run(
        svc.handle_targeted_order_message(
            message("Order Egg Biryani for me from BiryaniByKilo and it should reach by 8PM")
        )
    )

    assert "scheduled" in reply.lower()
    orders = run(svc.db.list_orders_for_host("919988776655"))
    assert len(orders) == 1
    order = orders[0]
    assert order.status == OrderStatus.SCHEDULED
    assert order.swiggy_order_id is None
    assert order.delivery_deadline is not None
    assert order.target_placement_at == order.delivery_deadline - timedelta(minutes=45)


def test_restaurant_not_found_creates_no_order() -> None:
    svc = service()

    reply = run(
        svc.handle_targeted_order_message(message("Order pizza from NoSuchPlace restaurant"))
    )

    assert "couldn't find a restaurant" in reply
    assert run(svc.db.list_orders_for_host("919988776655")) == []


def test_dish_not_found_creates_no_order() -> None:
    svc = service()

    reply = run(
        svc.handle_targeted_order_message(
            message("Order some nonexistent dish from MotiMahal restaurant")
        )
    )

    assert "Couldn't find" in reply
    assert run(svc.db.list_orders_for_host("919988776655")) == []


def test_duplicate_source_message_id_is_idempotent() -> None:
    svc = service()
    msg = message("Order paneer tikka from MotiMahal restaurant", message_id="wamid.dup")

    first_reply = run(svc.handle_targeted_order_message(msg))
    second_reply = run(svc.handle_targeted_order_message(msg))

    assert "Placed!" in first_reply
    assert "Already placed" in second_reply
    assert len(run(svc.db.list_orders_for_host("919988776655"))) == 1
