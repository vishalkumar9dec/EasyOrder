import asyncio

from fastapi.testclient import TestClient

from app.main import create_app
from app.models.session import CartItem, DietaryTag, Vertical, hash_host_token
from app.models.whatsapp import IncomingMessage
from app.services.mock_agent import MockAgentService
from app.services.mock_swiggy import MockSwiggyMcpClient, MockSwiggyScenario


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


def test_host_can_validate_checkout_with_grouped_steps() -> None:
    app, result = create_initialized_session()
    client = TestClient(app)

    validation = client.post(
        f"/api/session/{result.session.session_id}/checkout",
        params={"token": result.host_token},
    )

    assert validation.status_code == 200
    body = validation.json()
    assert body["checkout_ready"] is True
    assert body["status"] == "checkout_ready"
    assert [group["vertical"] for group in body["groups"]] == ["food", "instamart"]
    assert body["groups"][0]["source_label"] == "Biryani House"
    assert body["groups"][1]["source_label"] == "Instamart Mock Store"

    refreshed = client.get(
        f"/api/session/{result.session.session_id}",
        params={"token": result.host_token},
    )
    assert refreshed.json()["status"] == "CHECKOUT_READY"


def test_guest_cannot_validate_checkout() -> None:
    app, result = create_initialized_session()

    response = TestClient(app).post(
        f"/api/session/{result.session.session_id}/checkout",
        params={"token": result.session.guest_token},
    )

    assert response.status_code == 403
    assert response.json()["detail"] == "Only the host can validate checkout"


def test_checkout_validation_returns_unavailable_item_conflict() -> None:
    app, result = create_initialized_session()
    app.state.swiggy_client = MockSwiggyMcpClient(
        MockSwiggyScenario(unavailable_item_id="im-cola")
    )

    response = TestClient(app).post(
        f"/api/session/{result.session.session_id}/checkout",
        params={"token": result.host_token},
    )

    assert response.status_code == 409
    detail = response.json()["detail"]
    assert detail["checkout_ready"] is False
    assert detail["issues"][0]["code"] == "ITEM_UNAVAILABLE"
    assert detail["issues"][0]["item_id"] == "im-cola"
    assert detail["issues"][0]["source_label"] == "Instamart Mock Store"
    assert detail["issues"][0]["substitutes"][0]["source_label"] == "Instamart Mock Store"


def test_checkout_validation_returns_price_change_conflict() -> None:
    app, result = create_initialized_session()
    app.state.swiggy_client = MockSwiggyMcpClient(
        MockSwiggyScenario(price_change_item_id="food-chicken-biryani")
    )

    response = TestClient(app).post(
        f"/api/session/{result.session.session_id}/checkout",
        params={"token": result.host_token},
    )

    assert response.status_code == 409
    detail = response.json()["detail"]
    assert detail["issues"][0]["code"] == "PRICE_CHANGED"
    assert detail["issues"][0]["item_id"] == "food-chicken-biryani"
    assert detail["issues"][0]["new_price"] == "645.00"


def test_checkout_validation_groups_multiple_food_restaurants() -> None:
    app, result = create_initialized_session("@EasyOrder get pizza for 3 under 3000")
    client = TestClient(app)
    add_response = client.post(
        f"/api/session/{result.session.session_id}/cart-items",
        params={"token": result.host_token},
        json={
            "name": "Masala dosa",
            "quantity": 2,
            "price": "140.00",
            "dietary_tag": "VEG",
            "vertical": "food",
            "restaurant_id": "rest-dosa-corner",
            "restaurant_name": "Dosa Corner",
        },
    )
    assert add_response.status_code == 201

    validation = client.post(
        f"/api/session/{result.session.session_id}/checkout",
        params={"token": result.host_token},
    )

    assert validation.status_code == 200
    groups = validation.json()["groups"]
    food_groups = [group for group in groups if group["vertical"] == "food"]
    assert [group["source_label"] for group in food_groups] == ["Dosa Corner", "Pizza Yard"]
    assert validation.json()["groups"][-1]["vertical"] == "instamart"


def test_host_can_confirm_checkout_with_sequential_urls() -> None:
    app, result = create_initialized_session()
    client = TestClient(app)

    response = client.post(
        f"/api/session/{result.session.session_id}/checkout/confirm",
        params={"token": result.host_token},
        json={"oauth_code": "mock-oauth-code"},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "created"
    assert body["checkout_complete"] is True
    assert body["partial_success"] is False
    assert [step["status"] for step in body["steps"]] == ["created", "created"]
    assert body["steps"][0]["checkout_url"].endswith("/food/rest-biryani-house/normal")
    assert body["steps"][1]["checkout_url"].endswith("/instamart/instamart/normal")

    refreshed = client.get(
        f"/api/session/{result.session.session_id}",
        params={"token": result.host_token},
    )
    assert refreshed.json()["status"] == "ORDERED"


def test_guest_cannot_confirm_checkout() -> None:
    app, result = create_initialized_session()

    response = TestClient(app).post(
        f"/api/session/{result.session.session_id}/checkout/confirm",
        params={"token": result.session.guest_token},
        json={"oauth_code": "mock-oauth-code"},
    )

    assert response.status_code == 403
    assert response.json()["detail"] == "Only the host can confirm checkout"


def test_checkout_confirm_groups_multiple_food_restaurants_sequentially() -> None:
    app, result = create_initialized_session("@EasyOrder get pizza for 3 under 3000")
    client = TestClient(app)
    add_response = client.post(
        f"/api/session/{result.session.session_id}/cart-items",
        params={"token": result.host_token},
        json={
            "name": "Masala dosa",
            "quantity": 2,
            "price": "140.00",
            "dietary_tag": "VEG",
            "vertical": "food",
            "restaurant_id": "rest-dosa-corner",
            "restaurant_name": "Dosa Corner",
        },
    )
    assert add_response.status_code == 201

    response = client.post(
        f"/api/session/{result.session.session_id}/checkout/confirm",
        params={"token": result.host_token},
        json={"oauth_code": "mock-oauth-code"},
    )

    assert response.status_code == 200
    steps = response.json()["steps"]
    assert [step["source_label"] for step in steps] == [
        "Dosa Corner",
        "Pizza Yard",
        "Instamart Mock Store",
    ]
    assert steps[0]["checkout_url"].endswith("/food/rest-dosa-corner/normal")
    assert steps[1]["checkout_url"].endswith("/food/rest-pizza-yard/normal")


def test_checkout_confirm_skips_empty_verticals() -> None:
    app, result = create_initialized_session()
    food_only = [
        item for item in result.session.cart_items if item.vertical == Vertical.FOOD
    ]
    run(app.state.db_adapter.update_cart_items(result.session.session_id, food_only))

    food_response = TestClient(app).post(
        f"/api/session/{result.session.session_id}/checkout/confirm",
        params={"token": result.host_token},
        json={"oauth_code": "mock-oauth-code"},
    )

    assert food_response.status_code == 200
    assert [step["vertical"] for step in food_response.json()["steps"]] == ["food"]

    instamart_only = [
        CartItem(
            item_id="im-cola",
            name="Cola 2L bottle",
            quantity=2,
            price="110.00",
            added_by="host",
            dietary_tag=DietaryTag.VEG,
            vertical=Vertical.INSTAMART,
            brand_name="Thums Up",
            source_label="Instamart Mock Store",
        )
    ]
    run(app.state.db_adapter.update_cart_items(result.session.session_id, instamart_only))
    run(app.state.db_adapter.update_session_status(result.session.session_id, "CHECKOUT_READY"))

    instamart_response = TestClient(app).post(
        f"/api/session/{result.session.session_id}/checkout/confirm",
        params={"token": result.host_token},
        json={"oauth_code": "mock-oauth-code"},
    )

    assert instamart_response.status_code == 200
    assert [step["vertical"] for step in instamart_response.json()["steps"]] == ["instamart"]


def test_checkout_confirm_reports_oauth_failure() -> None:
    app, result = create_initialized_session()

    response = TestClient(app).post(
        f"/api/session/{result.session.session_id}/checkout/confirm",
        params={"token": result.host_token},
        json={"oauth_code": "mock-oauth-fail"},
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "Swiggy OAuth exchange failed"


def test_checkout_confirm_reports_partial_failure() -> None:
    app, result = create_initialized_session()
    app.state.swiggy_client = MockSwiggyMcpClient(
        MockSwiggyScenario(cart_failure_vertical="instamart")
    )

    response = TestClient(app).post(
        f"/api/session/{result.session.session_id}/checkout/confirm",
        params={"token": result.host_token},
        json={"oauth_code": "mock-oauth-code"},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "partial"
    assert body["checkout_complete"] is False
    assert body["partial_success"] is True
    assert [step["status"] for step in body["steps"]] == ["created", "failed"]

    refreshed = TestClient(app).get(
        f"/api/session/{result.session.session_id}",
        params={"token": result.host_token},
    )
    assert refreshed.json()["status"] == "CHECKOUT_PARTIAL"
