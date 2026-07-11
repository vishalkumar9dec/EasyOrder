from app.models.whatsapp import IncomingMessage
from app.services.intent_router import (
    ChatMode,
    IntentFamily,
    classify_chat_mode,
    route_business_chat_message,
)


def make_message(text: str, *, tagged: bool = False, phone_number_id: str = "business-42"):
    return IncomingMessage(
        sender_id="919988776655",
        message_id="wamid.router-test",
        message_text=text,
        phone_number_id=phone_number_id,
        timestamp="1782489000",
        is_easyorder_tagged=tagged,
    )


def test_tagged_message_is_mention_planning_everywhere() -> None:
    message = make_message("@EasyOrder get biryani for 4", tagged=True, phone_number_id="group-1")

    mode = classify_chat_mode(
        message, business_phone_number_id="business-42", business_chat_enabled=True
    )

    assert mode == ChatMode.MENTION_PLANNING


def test_untagged_direct_message_to_business_number_is_business_chat() -> None:
    message = make_message("what was my last order?")

    mode = classify_chat_mode(
        message, business_phone_number_id="business-42", business_chat_enabled=True
    )

    assert mode == ChatMode.BUSINESS_CHAT


def test_untagged_group_message_stays_passive() -> None:
    message = make_message("what was my last order?", phone_number_id="group_ipl_fans_1")

    mode = classify_chat_mode(
        message, business_phone_number_id="business-42", business_chat_enabled=True
    )

    assert mode == ChatMode.GROUP_PASSIVE


def test_business_chat_disabled_or_unconfigured_stays_passive() -> None:
    message = make_message("what was my last order?")

    disabled = classify_chat_mode(
        message, business_phone_number_id="business-42", business_chat_enabled=False
    )
    unconfigured = classify_chat_mode(
        message, business_phone_number_id="", business_chat_enabled=True
    )

    assert disabled == ChatMode.GROUP_PASSIVE
    assert unconfigured == ChatMode.GROUP_PASSIVE


def test_greeting_routes_to_onboarding_without_session() -> None:
    routed = route_business_chat_message("Get started")

    assert routed.family == IntentFamily.START_SESSION
    assert routed.creates_session is False
    assert "@EasyOrder" in routed.reply_text


def test_order_history_question_routes_to_history_intent() -> None:
    for text in ("what was my last order?", "when will my order arrive?", "order status"):
        routed = route_business_chat_message(text)
        assert routed.family == IntentFamily.ORDER_HISTORY_STATUS, text
        assert routed.creates_session is False
        assert "coming soon" in routed.reply_text


def test_discovery_question_routes_to_discovery_intent() -> None:
    for text in ("nearest best chole bhature", "any offers today?", "recommend a pizza place"):
        routed = route_business_chat_message(text)
        assert routed.family == IntentFamily.DISCOVERY_OFFERS, text
        assert routed.creates_session is False


def test_saved_list_command_routes_to_saved_list_intent() -> None:
    for text in ("add vim bar to monthly", "show monthly list", "remove vim bar from monthly"):
        routed = route_business_chat_message(text)
        assert routed.family == IntentFamily.SAVED_LIST_COMMAND, text
        assert routed.creates_session is False


def test_share_request_routes_to_share_intent_unconfirmed() -> None:
    routed = route_business_chat_message("share the order details")

    assert routed.family == IntentFamily.SHARE_REQUEST
    assert routed.creates_session is False
    assert routed.share_confirmed is False


def test_share_confirmation_grammar_unlocks_confirmed_share() -> None:
    for text in ("share yes", "yes share it", "confirm share", "share go ahead"):
        routed = route_business_chat_message(text)
        assert routed.family == IntentFamily.SHARE_REQUEST, text
        assert routed.share_confirmed is True, text


def test_order_request_creates_planning_session() -> None:
    for text in ("get biryani for 4 under 2000", "order 2 pizzas", "need snacks for 6"):
        routed = route_business_chat_message(text)
        assert routed.family == IntentFamily.START_SESSION, text
        assert routed.creates_session is True
        assert routed.reply_text is None


def test_gibberish_routes_to_unsupported_with_safe_reply() -> None:
    routed = route_business_chat_message("asdf qwerty")

    assert routed.family == IntentFamily.UNSUPPORTED
    assert routed.creates_session is False
    assert "for example" in routed.reply_text
