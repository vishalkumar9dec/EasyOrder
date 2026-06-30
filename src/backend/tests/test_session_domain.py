from decimal import Decimal

import pytest
from pydantic import ValidationError

from app.models.session import (
    CartItem,
    DietaryTag,
    GeneratedSessionTokens,
    SessionCreate,
    SessionStatus,
    Vertical,
    generate_session_tokens,
    hash_host_token,
)


def test_session_create_uses_lld_defaults() -> None:
    session = SessionCreate(whatsapp_group_id="group_ipl_fans_1", host_phone="919988776655")

    assert session.budget_limit == Decimal("3000.00")
    assert session.head_count == 4
    assert session.dietary_preference == DietaryTag.ANY
    assert session.status == SessionStatus.INITIALIZING
    assert session.budget_warning is False
    assert session.degraded_verticals == []


def test_cart_item_rejects_invalid_enum_values() -> None:
    with pytest.raises(ValidationError):
        CartItem(
            item_id="dish-1",
            name="Paneer rolls",
            price=180,
            added_by="guest_1",
            dietary_tag="EGG",
            vertical="food",
            restaurant_id="rest-1",
            restaurant_name="Roll House",
        )

    with pytest.raises(ValidationError):
        CartItem(
            item_id="dish-1",
            name="Paneer rolls",
            price=180,
            added_by="guest_1",
            dietary_tag="VEG",
            vertical="pharmacy",
        )


def test_cart_item_requires_source_attribution_for_supported_verticals() -> None:
    with pytest.raises(ValidationError):
        CartItem(
            item_id="food-paneer-roll",
            name="Paneer tikka rolls",
            price=180,
            added_by="guest_1",
            dietary_tag=DietaryTag.VEG,
            vertical=Vertical.FOOD,
        )

    with pytest.raises(ValidationError):
        CartItem(
            item_id="im-cola",
            name="Cola 2L bottle",
            price=110,
            added_by="guest_1",
            dietary_tag=DietaryTag.VEG,
            vertical=Vertical.INSTAMART,
        )


def test_session_token_generation_hashes_host_token_and_keeps_guest_public() -> None:
    tokens = generate_session_tokens()

    assert isinstance(tokens, GeneratedSessionTokens)
    assert tokens.host_token.startswith("host_")
    assert tokens.guest_token.startswith("guest_")
    assert tokens.host_token != tokens.host_token_hash
    assert tokens.host_token not in tokens.host_token_hash
    assert tokens.host_token_hash == hash_host_token(tokens.host_token)
    assert len(tokens.host_token_hash) == 64


def test_cart_item_normalizes_price_and_accepts_supported_values() -> None:
    item = CartItem(
        item_id="food-paneer-roll",
        name="Paneer tikka rolls",
        quantity=4,
        price="180",
        added_by="919988776655",
        dietary_tag=DietaryTag.VEG,
        vertical=Vertical.FOOD,
        restaurant_id="rest-roll-house",
        restaurant_name="Roll House",
    )

    assert item.price == Decimal("180.00")
    assert item.quantity == 4
    assert item.restaurant_name == "Roll House"
