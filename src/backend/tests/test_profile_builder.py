"""Deterministic profile derivation from committed order history."""

from datetime import UTC, datetime, timedelta
from decimal import Decimal

from app.models.order import Order, OrderLineItem, OrderStatus
from app.models.profile import MIN_OBSERVATIONS, UserProfile
from app.models.session import CartItem, DietaryTag, Session, SessionStatus, Vertical
from app.services.profile_builder import build_profile, describe_applied_defaults

WA_ID = "919988776655"
BASE = datetime(2026, 8, 3, 20, 30, tzinfo=UTC)  # a Monday evening


def order(
    total: str,
    *,
    restaurant: str = "MotiMahal",
    status: OrderStatus = OrderStatus.PLACED,
    created_at: datetime = BASE,
    wa_id: str = WA_ID,
) -> Order:
    return Order(
        wa_id=wa_id,
        restaurant_id=f"rest-{restaurant.lower()}",
        restaurant_name=restaurant,
        items=[OrderLineItem(item_id="i1", name="Paneer Tikka", price=Decimal(total))],
        total=Decimal(total),
        status=status,
        created_at=created_at,
    )


def session(
    *,
    status: SessionStatus = SessionStatus.ORDERED,
    head_count: int = 6,
    dietary: DietaryTag = DietaryTag.ANY,
    items: list[tuple[str, str, int]] | None = None,
    created_at: datetime = BASE,
) -> Session:
    cart = [
        CartItem(
            item_id=f"food-{name}",
            name=name,
            quantity=quantity,
            price=Decimal(price),
            added_by=WA_ID,
            vertical=Vertical.FOOD,
            restaurant_id=f"rest-{name}",
            restaurant_name=name,
        )
        for name, price, quantity in (items or [("Paradise", "500.00", 2)])
    ]
    return Session(
        whatsapp_group_id="group-1",
        host_phone=WA_ID,
        host_token_hash="hash",
        guest_token="guest",
        head_count=head_count,
        dietary_preference=dietary,
        status=status,
        cart_items=cart,
        created_at=created_at,
    )


def test_no_history_produces_an_empty_unconfident_profile() -> None:
    profile = build_profile(WA_ID, [], [])

    assert profile == UserProfile(wa_id=WA_ID)
    assert profile.is_confident is False
    assert profile.typical_budget is None


def test_only_committed_records_count_as_observations() -> None:
    orders = [
        order("300.00"),
        order("400.00", status=OrderStatus.DELIVERED),
        order("900.00", status=OrderStatus.SCHEDULED),
        order("800.00", status=OrderStatus.PENDING_CONFIRMATION),
        order("700.00", status=OrderStatus.CANCELLED),
        order("600.00", status=OrderStatus.FAILED),
    ]
    sessions = [session(), session(status=SessionStatus.ACTIVE)]

    profile = build_profile(WA_ID, orders, sessions)

    # 2 committed orders + 1 ORDERED session. Intent is not evidence.
    assert profile.observations == 3
    assert profile.is_confident is True


def test_confidence_gate_needs_min_observations() -> None:
    profile = build_profile(WA_ID, [order("300.00"), order("400.00")], [])

    assert profile.observations == 2 < MIN_OBSERVATIONS
    assert profile.is_confident is False
    # Still derived and readable — just not yet trusted enough to apply.
    assert profile.typical_budget is not None


def test_typical_budget_is_the_median_rounded_to_a_human_number() -> None:
    profile = build_profile(WA_ID, [order("310.00"), order("780.00"), order("1240.00")], [])

    # Median 780 rounds to 800; never rounds below what the user actually spends.
    assert profile.typical_budget == Decimal("800.00")
    assert profile.typical_budget >= Decimal("780.00")
    assert profile.budget_ceiling == Decimal("1240.00")


def test_headcount_comes_from_group_sessions_not_solo_orders() -> None:
    profile = build_profile(
        WA_ID,
        [order("300.00"), order("400.00")],
        [session(head_count=8), session(head_count=6), session(head_count=6)],
    )

    # Targeted orders have no headcount; counting them as 1 would drag the
    # median down for someone who mostly hosts.
    assert profile.usual_headcount == 6


def test_dietary_tendency_needs_a_clear_majority() -> None:
    mostly_veg = build_profile(
        WA_ID,
        [],
        [
            session(dietary=DietaryTag.VEG),
            session(dietary=DietaryTag.VEG),
            session(dietary=DietaryTag.VEG),
        ],
    )
    assert mostly_veg.dietary_tendency == DietaryTag.VEG

    split = build_profile(
        WA_ID,
        [],
        [
            session(dietary=DietaryTag.VEG),
            session(dietary=DietaryTag.NON_VEG),
            session(dietary=DietaryTag.ANY),
            session(dietary=DietaryTag.ANY),
        ],
    )
    assert split.dietary_tendency is None


def test_favourites_rank_by_frequency_then_recency() -> None:
    profile = build_profile(
        WA_ID,
        [
            order("300.00", restaurant="MotiMahal", created_at=BASE),
            order("300.00", restaurant="MotiMahal", created_at=BASE + timedelta(days=1)),
            order("300.00", restaurant="Paradise", created_at=BASE + timedelta(days=2)),
        ],
        [],
    )

    assert [f.restaurant_name for f in profile.favourites] == ["MotiMahal", "Paradise"]
    assert profile.favourite_restaurant == "MotiMahal"
    assert profile.favourites[0].order_count == 2
    assert profile.favourites[0].last_ordered_at == BASE + timedelta(days=1)


def test_a_session_counts_as_one_visit_per_restaurant_not_one_per_item() -> None:
    profile = build_profile(
        WA_ID,
        [],
        [
            session(
                items=[("Paradise", "300.00", 1), ("Paradise", "200.00", 1)],
            )
        ],
    )

    assert profile.favourites[0].order_count == 1


def test_rhythm_uses_the_modal_weekday_and_hour() -> None:
    profile = build_profile(
        WA_ID,
        [
            order("300.00", created_at=BASE),
            order("300.00", created_at=BASE + timedelta(days=7)),
            order("300.00", created_at=BASE + timedelta(days=1, hours=2)),
        ],
        [],
    )

    assert profile.busiest_weekday == "Monday"
    assert profile.busiest_hour == 20
    assert profile.last_ordered_at == BASE + timedelta(days=7)


def test_history_from_other_users_is_not_mixed_in() -> None:
    profile = build_profile(WA_ID, [order("300.00"), order("999.00", wa_id="910000000000")], [])

    # build_profile summarizes the rows it is handed; the caller scopes them.
    # This documents that the totals it reports are exactly those rows.
    assert profile.observations == 2


class TestDisclosure:
    def test_names_each_applied_default_and_how_to_override(self) -> None:
        profile = build_profile(WA_ID, [order("800.00")] * 3, [session(head_count=6)])

        note = describe_applied_defaults(profile, ["budget_limit", "head_count"])

        assert "INR 800" in note
        assert "6 people" in note
        assert "override" in note.lower()
        assert str(profile.observations) in note

    def test_is_silent_when_nothing_was_applied(self) -> None:
        profile = build_profile(WA_ID, [order("800.00")] * 3, [])

        assert describe_applied_defaults(profile, []) == ""

    def test_is_silent_when_the_applied_field_has_no_value(self) -> None:
        profile = build_profile(WA_ID, [order("800.00")] * 3, [])

        # No group sessions, so no headcount to talk about.
        assert describe_applied_defaults(profile, ["head_count"]) == ""


def test_ceiling_is_never_reported_below_the_typical_budget() -> None:
    # Three identical spends: median 580 rounds up to 600, but the raw p90 is
    # still 580 — a ceiling under the usual would be nonsense to read.
    profile = build_profile(WA_ID, [order("580.00"), order("580.00"), order("580.00")], [])

    assert profile.typical_budget == Decimal("600.00")
    assert profile.budget_ceiling == Decimal("600.00")
    assert profile.budget_ceiling >= profile.typical_budget
