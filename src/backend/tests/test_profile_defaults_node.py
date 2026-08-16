"""The profile_defaults graph node: fills the unsaid, never the said."""

import asyncio
from decimal import Decimal

from app.models.order import OrderCreate, OrderLineItem, OrderStatus
from app.models.session import DietaryTag, SessionStatus
from app.models.whatsapp import IncomingMessage
from app.services.agent import EasyOrderAgentService, EasyOrderState
from app.services.memory_db import InMemoryDBAdapter
from app.services.mock_swiggy import MockSwiggyMcpClient

WA_ID = "919988776655"


def run(coro):
    return asyncio.run(coro)


def message(text: str, *, sender_id: str = WA_ID) -> IncomingMessage:
    return IncomingMessage(
        sender_id=sender_id,
        message_id=f"wamid.{abs(hash(text)) % 10**8}",
        message_text=text,
        phone_number_id="biz-1",
        timestamp="1782489000",
        is_easyorder_tagged=True,
    )


def service_with_history(
    *,
    orders: int = 0,
    order_total: str = "800.00",
    sessions: int = 0,
    head_count: int = 6,
    dietary: DietaryTag = DietaryTag.ANY,
) -> EasyOrderAgentService:
    """An agent whose database already holds this user's committed history."""
    db = InMemoryDBAdapter()
    for index in range(orders):
        run(
            db.create_order(
                OrderCreate(
                    wa_id=WA_ID,
                    restaurant_id="rest-moti",
                    restaurant_name="MotiMahal",
                    items=[
                        OrderLineItem(
                            item_id=f"i{index}", name="Tikka", price=Decimal(order_total)
                        )
                    ],
                    total=Decimal(order_total),
                    status=OrderStatus.PLACED,
                )
            )
        )
    for _ in range(sessions):
        created = run(
            db.create_session(
                _session_create(head_count=head_count, dietary=dietary),
                host_token_hash="hash",
                guest_token="guest",
            )
        )
        run(db.update_session_status(created.session_id, SessionStatus.ORDERED))
    return EasyOrderAgentService(db=db, swiggy_client=MockSwiggyMcpClient())


def _session_create(*, head_count: int, dietary: DietaryTag):
    from app.models.session import SessionCreate

    return SessionCreate(
        whatsapp_group_id="group-1",
        host_phone=WA_ID,
        head_count=head_count,
        dietary_preference=dietary,
    )


async def _intent_after_profile(service: EasyOrderAgentService, text: str):
    state = EasyOrderState(message=message(text))
    state = await service.apply_input_guardrails(state)
    state = await service.parse_intent(state)
    return await service.apply_profile_defaults(state)


def test_a_new_user_gets_the_stock_defaults_untouched() -> None:
    service = service_with_history()

    state = run(_intent_after_profile(service, "get biryani"))

    assert state.applied_defaults == []
    assert state.intent.budget_limit == Decimal("3000")
    assert state.intent.head_count == 4


def test_thin_history_is_derived_but_not_applied() -> None:
    service = service_with_history(orders=2, order_total="800.00")

    state = run(_intent_after_profile(service, "get biryani"))

    assert state.profile.observations == 2
    assert state.profile.is_confident is False
    assert state.applied_defaults == []
    assert state.intent.budget_limit == Decimal("3000")


def test_learned_budget_fills_a_prompt_that_never_named_one() -> None:
    service = service_with_history(orders=3, order_total="800.00")

    state = run(_intent_after_profile(service, "get biryani"))

    assert "budget_limit" in state.applied_defaults
    assert state.intent.budget_limit == Decimal("800.00")


def test_an_explicit_budget_is_never_overwritten() -> None:
    service = service_with_history(orders=3, order_total="800.00")

    state = run(_intent_after_profile(service, "get biryani under 2000"))

    assert "budget_limit" not in state.applied_defaults
    assert state.intent.budget_limit == Decimal("2000")


def test_an_explicit_headcount_is_never_overwritten() -> None:
    service = service_with_history(orders=3, sessions=3, head_count=8)

    state = run(_intent_after_profile(service, "get biryani for 2"))

    assert "head_count" not in state.applied_defaults
    assert state.intent.head_count == 2


def test_an_explicit_dietary_preference_is_never_overwritten() -> None:
    service = service_with_history(orders=1, sessions=3, dietary=DietaryTag.VEG)

    state = run(_intent_after_profile(service, "get chicken biryani"))

    assert "dietary_preference" not in state.applied_defaults
    assert state.intent.dietary_preference == DietaryTag.NON_VEG


def test_learned_headcount_and_diet_fill_a_bare_prompt() -> None:
    service = service_with_history(orders=1, sessions=3, head_count=8, dietary=DietaryTag.VEG)

    state = run(_intent_after_profile(service, "get biryani"))

    assert set(state.applied_defaults) >= {"head_count", "dietary_preference"}
    assert state.intent.head_count == 8
    assert state.intent.dietary_preference == DietaryTag.VEG


def test_one_users_habits_never_leak_into_anothers_order() -> None:
    service = service_with_history(orders=3, order_total="800.00")

    state = EasyOrderState(message=message("get biryani", sender_id="910000000000"))
    state = run(service.apply_input_guardrails(state))
    state = run(service.parse_intent(state))
    state = run(service.apply_profile_defaults(state))

    assert state.profile.observations == 0
    assert state.applied_defaults == []
    assert state.intent.budget_limit == Decimal("3000")


def test_a_broken_profile_read_never_blocks_the_order() -> None:
    service = service_with_history(orders=3)

    async def exploding_list(*_args, **_kwargs):
        raise RuntimeError("database is having a moment")

    service.db.list_orders_for_host = exploding_list

    state = run(_intent_after_profile(service, "get biryani"))

    # Personalization is an improvement to the order, not a precondition for it.
    assert state.applied_defaults == []
    assert state.errors == []
    assert state.intent.budget_limit == Decimal("3000")


def test_the_node_runs_between_parsing_and_the_swiggy_workers() -> None:
    service = service_with_history()

    assert [name for name, _ in service.build_graph().nodes] == [
        "input_guardrails",
        "intent_parser",
        "profile_defaults",
        "swiggy_workers",
        "output_guardrails",
        "persistence",
    ]
