"""GET /api/me/spend — committed spend across both order surfaces."""

import asyncio
from decimal import Decimal

from fastapi.testclient import TestClient

from app.config import get_settings
from app.main import app
from app.models.order import OrderCreate, OrderLineItem, OrderStatus
from app.models.session import SessionStatus
from app.services.web_auth import normalize_phone
from tests.test_account_api import login
from tests.test_whatsapp_webhook import business_chat_settings, whatsapp_payload


def run(coro):
    return asyncio.run(coro)


def order_payload(
    wa_id: str,
    *,
    total: str,
    status: OrderStatus,
    restaurant: str = "MotiMahal",
) -> OrderCreate:
    return OrderCreate(
        wa_id=wa_id,
        restaurant_id="rest-1",
        restaurant_name=restaurant,
        items=[OrderLineItem(item_id="item-1", name="Paneer Tikka", price=Decimal(total))],
        total=Decimal(total),
        status=status,
    )


def test_my_spend_requires_login() -> None:
    client = TestClient(app)

    assert client.get("/api/me/spend").status_code == 401


def test_my_spend_counts_only_committed_money() -> None:
    db = app.state.db_adapter
    client = TestClient(app)
    phone = "+91 99880 00051"
    wa_id = normalize_phone(phone)

    # Placed and delivered are spend; scheduled, pending, cancelled and failed are not.
    for payload in (
        order_payload(wa_id, total="300.00", status=OrderStatus.PLACED),
        order_payload(wa_id, total="250.50", status=OrderStatus.DELIVERED),
        order_payload(wa_id, total="900.00", status=OrderStatus.SCHEDULED),
        order_payload(wa_id, total="700.00", status=OrderStatus.PENDING_CONFIRMATION),
        order_payload(wa_id, total="500.00", status=OrderStatus.CANCELLED),
        order_payload(wa_id, total="400.00", status=OrderStatus.FAILED),
    ):
        run(db.create_order(payload))

    login(client, phone)
    body = client.get("/api/me/spend").json()

    assert body["wa_id"] == wa_id
    assert body["currency"] == "INR"
    assert body["restaurant_orders"] == {"total": "550.50", "count": 2}
    assert body["total"] == "550.50"
    assert body["order_count"] == 2


def test_my_spend_includes_ordered_group_sessions_only() -> None:
    db = app.state.db_adapter
    client = TestClient(app)
    phone = "+91 99880 00052"
    wa_id = normalize_phone(phone)

    app.dependency_overrides[get_settings] = business_chat_settings
    try:
        for index in (1, 2):
            created = client.post(
                "/api/whatsapp/webhook",
                json=whatsapp_payload(
                    "get biryani for 4 under 2000",
                    message_id=f"wamid.spend.session.{index}",
                    phone_number_id="business-42",
                    sender_wa_id=wa_id,
                ),
            )
            assert created.status_code == 200
    finally:
        app.dependency_overrides.pop(get_settings, None)

    sessions = run(db.list_sessions_for_host(wa_id))
    assert len(sessions) == 2
    placed, still_planning = sessions
    run(db.update_session_status(placed.session_id, SessionStatus.ORDERED))
    placed_total = sum(item.price * item.quantity for item in placed.cart_items)
    assert placed_total > 0
    assert still_planning.status != SessionStatus.ORDERED

    login(client, phone)
    body = client.get("/api/me/spend").json()

    # Only the ORDERED session counts; one still being planned is intent, not spend.
    assert body["group_orders"] == {"total": f"{placed_total:.2f}", "count": 1}
    assert body["total"] == f"{placed_total:.2f}"


def test_my_spend_is_isolated_per_user_and_zero_by_default() -> None:
    db = app.state.db_adapter
    client = TestClient(app)
    other_wa_id = normalize_phone("+91 99880 00053")
    run(db.create_order(order_payload(other_wa_id, total="999.00", status=OrderStatus.PLACED)))

    phone = "+91 99880 00054"
    login(client, phone)
    body = client.get("/api/me/spend").json()

    assert body["total"] == "0.00"
    assert body["order_count"] == 0
    assert body["group_orders"] == {"total": "0.00", "count": 0}
    assert body["restaurant_orders"] == {"total": "0.00", "count": 0}
