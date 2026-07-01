import asyncio

from fastapi.testclient import TestClient

from app.main import create_app
from app.models.session import hash_host_token
from app.models.whatsapp import IncomingMessage
from app.services.mock_agent import MockAgentService


def run(coro):
    return asyncio.run(coro)


def message(text: str = "@EasyOrder get biryani and drinks for 4 under 3000") -> IncomingMessage:
    return IncomingMessage(
        sender_id="919988776655",
        message_id="wamid.session-api",
        message_text=text,
        phone_number_id="group_ipl_fans_1",
        timestamp="1782489000",
        is_easyorder_tagged=True,
    )


def create_initialized_session(text: str = "@EasyOrder get biryani and drinks for 4 under 3000"):
    app = create_app()
    agent = app.state.agent_service
    assert isinstance(agent, MockAgentService)
    result = run(agent.initialize_tagged_message(message(text)))
    return app, result


def test_guest_token_bootstraps_redacted_session_state() -> None:
    app, result = create_initialized_session()

    response = TestClient(app).get(
        f"/api/session/{result.session.session_id}",
        params={"token": result.session.guest_token},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["session_id"] == result.session.session_id
    assert body["role"] == "guest"
    assert body["status"] == "ACTIVE"
    assert body["checkout_eligible"] is False
    assert body["cart_items"][0]["restaurant_id"]
    assert body["cart_items"][0]["restaurant_name"] == "Biryani House"
    assert body["cart_items"][1]["brand_name"] == "Thums Up"
    assert body["cart_items"][1]["source_label"] == "Instamart Mock Store"
    assert "guest_token" not in body
    assert "host_token" not in body
    assert "host_token_hash" not in body
    assert "host_phone" not in body


def test_host_token_bootstraps_host_role_without_exposing_token_material() -> None:
    app, result = create_initialized_session()

    response = TestClient(app).get(
        f"/api/session/{result.session.session_id}",
        params={"token": result.host_token},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["role"] == "host"
    assert body["checkout_eligible"] is True
    assert hash_host_token(result.host_token) == result.session.host_token_hash
    assert result.host_token not in response.text
    assert result.session.host_token_hash not in response.text


def test_invalid_or_cross_session_token_is_unauthorized() -> None:
    app, first = create_initialized_session()
    agent = app.state.agent_service
    second = run(agent.initialize_tagged_message(message("@EasyOrder get pizza for 3 under 1200")))

    invalid = TestClient(app).get(
        f"/api/session/{first.session.session_id}",
        params={"token": "guest_wrong"},
    )
    cross_session = TestClient(app).get(
        f"/api/session/{first.session.session_id}",
        params={"token": second.session.guest_token},
    )

    assert invalid.status_code == 401
    assert invalid.json()["detail"] == "Invalid session token"
    assert cross_session.status_code == 401


def test_missing_session_returns_not_found_before_authorization() -> None:
    app = create_app()

    response = TestClient(app).get("/api/session/session_missing", params={"token": "guest_any"})

    assert response.status_code == 404
    assert response.json()["detail"] == "Session not found"


def test_guest_can_create_update_and_delete_cart_item_for_session() -> None:
    app, result = create_initialized_session()
    client = TestClient(app)

    create_response = client.post(
        f"/api/session/{result.session.session_id}/cart-items",
        params={"token": result.session.guest_token},
        json={
            "name": "Paper napkins",
            "quantity": 3,
            "price": "45.00",
            "dietary_tag": "ANY",
            "vertical": "instamart",
            "brand_name": "PartyPro",
            "source_label": "Instamart Mock Store",
        },
    )

    assert create_response.status_code == 201
    created_body = create_response.json()
    created = created_body["cart_items"][-1]
    assert created["name"] == "Paper napkins"
    assert created["added_by"] == "guest"
    assert created["source_label"] == "Instamart Mock Store"

    update_response = client.patch(
        f"/api/session/{result.session.session_id}/cart-items/{created['id']}",
        params={"token": result.session.guest_token},
        json={"quantity": 5, "price": "42.00"},
    )

    assert update_response.status_code == 200
    updated = update_response.json()["cart_items"][-1]
    assert updated["id"] == created["id"]
    assert updated["quantity"] == 5
    assert updated["price"] == "42.00"

    delete_response = client.delete(
        f"/api/session/{result.session.session_id}/cart-items/{created['id']}",
        params={"token": result.session.guest_token},
    )

    assert delete_response.status_code == 200
    assert all(item["id"] != created["id"] for item in delete_response.json()["cart_items"])


def test_cart_mutation_rejects_cross_session_token() -> None:
    app, first = create_initialized_session()
    agent = app.state.agent_service
    second = run(agent.initialize_tagged_message(message("@EasyOrder get pizza for 3 under 1200")))

    response = TestClient(app).post(
        f"/api/session/{first.session.session_id}/cart-items",
        params={"token": second.session.guest_token},
        json={
            "name": "Plain dosa",
            "quantity": 1,
            "price": "120.00",
            "dietary_tag": "VEG",
            "vertical": "food",
            "restaurant_id": "rest-dosa-corner",
            "restaurant_name": "Dosa Corner",
        },
    )

    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid session token"


def test_cart_mutation_validates_source_attribution_and_missing_items() -> None:
    app, result = create_initialized_session()
    client = TestClient(app)

    missing_restaurant = client.post(
        f"/api/session/{result.session.session_id}/cart-items",
        params={"token": result.session.guest_token},
        json={
            "name": "Plain dosa",
            "quantity": 1,
            "price": "120.00",
            "dietary_tag": "VEG",
            "vertical": "food",
        },
    )
    missing_cart_item = client.patch(
        f"/api/session/{result.session.session_id}/cart-items/999999",
        params={"token": result.session.guest_token},
        json={"quantity": 2},
    )

    assert missing_restaurant.status_code == 422
    assert missing_cart_item.status_code == 404
    assert missing_cart_item.json()["detail"] == "Cart item not found"
