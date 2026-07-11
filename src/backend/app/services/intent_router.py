"""Deterministic chat-mode and intent routing for WhatsApp messages.

Two operating modes share the webhook (task 10.3):

- Mention-triggered planning: ``@EasyOrder`` messages, any chat. Unchanged.
- Dedicated business chat: untagged messages sent directly to the EasyOrder
  business number. Routed by intent family below, without requiring the tag.

Untagged messages that are not dedicated business chat (mock group ids, or
the feature disabled) stay ignored — ordinary group/passive listening is
explicitly out of scope (ADR 0003 privacy behavior).

Routing is deterministic keyword matching, mirroring the mock intent parser
precedent: predictable, testable, no LLM fallback yet.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from enum import StrEnum

from app.models.whatsapp import IncomingMessage


class ChatMode(StrEnum):
    """How an inbound message reached EasyOrder."""

    MENTION_PLANNING = "mention_planning"
    BUSINESS_CHAT = "business_chat"
    GROUP_PASSIVE = "group_passive"


class IntentFamily(StrEnum):
    """Intent families supported by the dedicated business chat."""

    START_SESSION = "start_session"
    SAVED_LIST_COMMAND = "saved_list_command"
    ORDER_HISTORY_STATUS = "order_history_status"
    DISCOVERY_OFFERS = "discovery_offers"
    SHARE_REQUEST = "share_request"
    UNSUPPORTED = "unsupported"


@dataclass(frozen=True)
class RoutedIntent:
    """Routing decision for one dedicated business-chat message."""

    family: IntentFamily
    # Canned reply for intents that do not create a session. None means the
    # message continues into the planning pipeline instead.
    reply_text: str | None
    creates_session: bool = False


EXAMPLE_PROMPT = "get biryani for 4 under 2000"

ONBOARDING_REPLY = (
    "Hi! I'm EasyOrder. Tell me what to order, for example: "
    f"{EXAMPLE_PROMPT}. In a group chat, tag @EasyOrder with the same request."
)
ORDER_HISTORY_REPLY = (
    "I can't look up your Swiggy order history or delivery status yet — "
    "that's coming soon. If you have an active EasyOrder session, open the "
    "link from our earlier message to review it."
)
DISCOVERY_REPLY = (
    "Restaurant discovery and offers are coming soon. For now, tell me what "
    f"to order, for example: {EXAMPLE_PROMPT}."
)
SAVED_LIST_REPLY = (
    "Saved lists are coming soon. For now, tell me what to order, for "
    f"example: {EXAMPLE_PROMPT}."
)
SHARE_REPLY = (
    "To share an order, open your session from our earlier message and tap "
    "Share with group."
)
UNSUPPORTED_REPLY = (
    "Sorry, I didn't catch that. Tell me what to order, for example: "
    f"{EXAMPLE_PROMPT}."
)

_GREETINGS = {
    "hi",
    "hello",
    "hey",
    "start",
    "get started",
    "help",
    "menu",
    "namaste",
}

_SAVED_LIST_PATTERNS = [
    re.compile(r"\badd\b.+\bto\b"),
    re.compile(r"\bshow\b.+\blist\b"),
    re.compile(r"\bremove\b.+\bfrom\b"),
    re.compile(r"\bmy\b.+\blists?\b"),
]

_HISTORY_PATTERNS = [
    re.compile(r"\blast order\b"),
    re.compile(r"\border (status|history)\b"),
    re.compile(r"\b(where|when).{0,30}\border\b"),
    re.compile(r"\border\b.{0,30}\b(arrive|arriving|delivered|delivery)\b"),
    re.compile(r"\btrack\b"),
]

_DISCOVERY_PATTERNS = [
    re.compile(r"\bnearest\b"),
    re.compile(r"\bnear me\b"),
    re.compile(r"\bbest\b"),
    re.compile(r"\boffers?\b"),
    re.compile(r"\bdiscounts?\b"),
    re.compile(r"\brecommend\b"),
    re.compile(r"\bsuggest\b"),
]

_ORDER_REQUEST_PATTERNS = [
    re.compile(r"\b(get|order|need|want|send)\b"),
    re.compile(r"\bunder\s+\d+"),
    re.compile(r"\bfor\s+\d+"),
]


def classify_chat_mode(
    message: IncomingMessage,
    *,
    business_phone_number_id: str,
    business_chat_enabled: bool,
) -> ChatMode:
    """Classify how the message reached EasyOrder.

    A message is dedicated business chat only when it is untagged AND arrived
    on the configured business phone number id. Mock group fixtures carry
    synthetic group ids, so they never match and remain passively ignored.
    """
    if message.is_easyorder_tagged:
        return ChatMode.MENTION_PLANNING
    if (
        business_chat_enabled
        and business_phone_number_id
        and message.phone_number_id == business_phone_number_id
    ):
        return ChatMode.BUSINESS_CHAT
    return ChatMode.GROUP_PASSIVE


def route_business_chat_message(message_text: str) -> RoutedIntent:
    """Route one dedicated business-chat message to an intent family."""
    normalized = message_text.strip().lower().rstrip("!.?")

    if normalized in _GREETINGS:
        return RoutedIntent(IntentFamily.START_SESSION, ONBOARDING_REPLY)
    if any(pattern.search(normalized) for pattern in _HISTORY_PATTERNS):
        return RoutedIntent(IntentFamily.ORDER_HISTORY_STATUS, ORDER_HISTORY_REPLY)
    if any(pattern.search(normalized) for pattern in _SAVED_LIST_PATTERNS):
        return RoutedIntent(IntentFamily.SAVED_LIST_COMMAND, SAVED_LIST_REPLY)
    if "share" in normalized:
        return RoutedIntent(IntentFamily.SHARE_REQUEST, SHARE_REPLY)
    if any(pattern.search(normalized) for pattern in _DISCOVERY_PATTERNS):
        return RoutedIntent(IntentFamily.DISCOVERY_OFFERS, DISCOVERY_REPLY)
    if any(pattern.search(normalized) for pattern in _ORDER_REQUEST_PATTERNS):
        return RoutedIntent(IntentFamily.START_SESSION, None, creates_session=True)
    return RoutedIntent(IntentFamily.UNSUPPORTED, UNSUPPORTED_REPLY)
