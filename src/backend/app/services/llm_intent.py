"""Real LLM-backed intent parsing for EasyOrder's agent.

Classifies a WhatsApp group-order prompt into the same ParsedIntent shape
MockIntentParser produces (budget, headcount, dietary preference, and
Food/Instamart search queries). That classification is what drives which
Swiggy MCP tools run_workers() calls next (search_restaurants and,
conditionally, search_instamart) — the LLM decides what to search for and
whether Instamart is in scope; the existing worker pipeline does the actual
MCP tool calls in realtime.
"""

from __future__ import annotations

import json
import logging
import re
from decimal import Decimal, InvalidOperation
from typing import Any

from openai import AsyncOpenAI

from app.models.session import DietaryTag
from app.services.agent import (
    IntentParser,
    MockIntentParser,
    MockTargetedOrderIntentParser,
    ParsedIntent,
    RequestedItem,
    TargetedOrderIntent,
    TargetedOrderIntentParser,
    extract_requested_items,
)

logger = logging.getLogger(__name__)


class LLMIntentConfigurationError(RuntimeError):
    """Raised when LLM_MODE=openai is selected without an API key."""


PARSED_INTENT_SCHEMA = {
    "name": "parsed_intent",
    "schema": {
        "type": "object",
        "properties": {
            "budget_limit": {
                "type": ["number", "null"],
                "description": (
                    "The budget in INR, exactly as the message states it — 'under 2000', "
                    "'budget of 2000', 'within 2000 rs' all mean 2000. null if the message "
                    "names no budget at all. Never invent a number to fill this in."
                ),
            },
            "head_count": {
                "type": ["integer", "null"],
                "description": (
                    "How many people the order is for, if the message says. null if it "
                    "does not. Never invent a headcount to fill this in."
                ),
            },
            "dietary_preference": {
                "type": "string",
                "enum": ["VEG", "NON-VEG", "ANY"],
            },
            "items": {
                "type": "array",
                "description": (
                    "Every dish the message names with an explicit count, in order. "
                    "Empty when the message names no counts, e.g. 'get biryani'."
                ),
                "items": {
                    "type": "object",
                    "properties": {
                        "name": {"type": "string"},
                        "quantity": {"type": "integer"},
                    },
                    "required": ["name", "quantity"],
                    "additionalProperties": False,
                },
            },
            "food_query": {
                "type": "string",
                "description": "Search terms to find dishes/restaurants on Swiggy Food.",
            },
            "wants_instamart": {
                "type": "boolean",
                "description": (
                    "True only if the message also asks for drinks, ice, plates, "
                    "napkins, or other grocery/party items beyond the food order."
                ),
            },
            "instamart_query": {
                "type": "string",
                "description": (
                    "Search terms for Swiggy Instamart. Empty string when "
                    "wants_instamart is false."
                ),
            },
        },
        "required": [
            "budget_limit",
            "head_count",
            "dietary_preference",
            "items",
            "food_query",
            "wants_instamart",
            "instamart_query",
        ],
        "additionalProperties": False,
    },
    "strict": True,
}

SYSTEM_PROMPT = (
    "You classify a WhatsApp group-order request for EasyOrder, a Swiggy ordering "
    "assistant. Extract the budget in INR, headcount, dietary preference, and what "
    "food to search for. List each dish that carries an explicit count in items, "
    "so a request for several dishes becomes several cart rows rather than one. "
    "Only set wants_instamart=true if the message separately "
    "asks for drinks, ice, plates, napkins, or similar grocery/party items. "
    "budget_limit and head_count must be null when the message does not state them — "
    "the caller applies its own defaults. Do not write a number to fill either field "
    "in; a filled-in default is worse than null, because it looks like something the "
    "user asked for."
)


class LLMIntentParser:
    """Parses prompts with a real LLM; falls back to the deterministic parser on any failure.

    A production assistant should not go fully dark because of an LLM outage,
    rate limit, or malformed response — falling back mirrors how the agent
    already degrades gracefully on Swiggy worker timeouts/failures.
    """

    def __init__(
        self,
        api_key: str,
        model: str,
        fallback: IntentParser | None = None,
        client: AsyncOpenAI | None = None,
    ) -> None:
        self._client = client or AsyncOpenAI(api_key=api_key)
        self._model = model
        self._fallback = fallback or MockIntentParser()

    async def parse(self, prompt: str) -> ParsedIntent:
        try:
            return await self._parse_with_llm(prompt)
        except Exception:
            logger.warning("llm_intent_parse_failed_falling_back_to_mock_parser", exc_info=True)
            return await self._fallback.parse(prompt)

    async def _parse_with_llm(self, prompt: str) -> ParsedIntent:
        response = await self._client.chat.completions.create(
            model=self._model,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": prompt},
            ],
            response_format={"type": "json_schema", "json_schema": PARSED_INTENT_SCHEMA},
        )
        content = response.choices[0].message.content
        if not content:
            raise ValueError("LLM returned no content")
        return _to_parsed_intent(json.loads(content), prompt)


# Applied only when the model reports the field as null. Matching
# MockIntentParser's literals so the two backends agree on what "unstated"
# defaults to.
_DEFAULT_BUDGET = Decimal("3000")
_DEFAULT_HEAD_COUNT = 4


def _to_parsed_intent(data: dict[str, Any], prompt: str = "") -> ParsedIntent:
    # budget_limit and head_count are nullable in the schema: null is the only
    # signal for "not stated", so there is nothing else that can disagree with
    # it. This replaced a pair of *_stated booleans the model reported
    # alongside an always-filled value — two outputs for one fact, which could
    # (and did) drift apart, e.g. head_count=4 with head_count_stated=false for
    # a message that plainly said "for 4".
    specified: set[str] = set()

    raw_budget = data.get("budget_limit")
    if raw_budget is None:
        budget_limit = _DEFAULT_BUDGET
    else:
        try:
            budget_limit = Decimal(str(raw_budget)).quantize(Decimal("0.01"))
        except InvalidOperation as error:
            raise ValueError("LLM response had an invalid budget_limit") from error
        specified.add("budget_limit")

    raw_head_count = data.get("head_count")
    if raw_head_count is None:
        head_count = _DEFAULT_HEAD_COUNT
    else:
        head_count = max(1, min(100, int(raw_head_count)))
        specified.add("head_count")

    dietary_preference = DietaryTag(str(data["dietary_preference"]))
    food_query = str(data["food_query"]).strip() or "food"
    instamart_query = str(data.get("instamart_query") or "").strip() or None
    if not data.get("wants_instamart"):
        instamart_query = None
    if dietary_preference != DietaryTag.ANY:
        specified.add("dietary_preference")

    llm_items = tuple(
        RequestedItem(
            name=str(entry["name"]).strip(),
            quantity=max(1, min(99, int(entry["quantity"]))),
        )
        for entry in (data.get("items") or [])
        if str(entry.get("name", "")).strip()
    )
    # "2 chicken biryani, 1 mixed veg and 3 tandoori roti" is a closed grammar
    # — quantity plus noun phrase, comma/and-separated — not open-vocabulary
    # language, so a regex parses it exactly where an LLM call only
    # approximates it. When the message matches that grammar, its result
    # replaces the model's item list outright rather than merging with it, so
    # the cart the demo's own scripted prompts produce carries zero model
    # variance. The LLM's list is used only when the message does not match —
    # free-form phrasing with no explicit per-item counts.
    regex_items = extract_requested_items(prompt)
    requested_items = regex_items or llm_items

    return ParsedIntent(
        budget_limit=budget_limit,
        head_count=head_count,
        dietary_preference=dietary_preference,
        food_query=food_query,
        instamart_query=instamart_query,
        requested_items=requested_items,
        specified=frozenset(specified),
    )


def create_intent_parser(*, mode: str, api_key: str, model: str) -> IntentParser:
    if mode == "openai":
        if not api_key:
            raise LLMIntentConfigurationError("OPENAI_API_KEY is required when LLM_MODE=openai")
        return LLMIntentParser(api_key=api_key, model=model)
    return MockIntentParser()


TARGETED_ORDER_INTENT_SCHEMA = {
    "name": "targeted_order_intent",
    "schema": {
        "type": "object",
        "properties": {
            "restaurant_name": {
                "type": "string",
                "description": "The single named restaurant the message asks to order from.",
            },
            "dish_names": {
                "type": "array",
                "items": {"type": "string"},
                "description": "The specific dish names requested, in the order mentioned.",
            },
            "budget_limit": {
                "type": ["number", "null"],
                "description": "Budget in INR that, if exceeded, requires confirmation before "
                "placing. Null when the message states no budget.",
            },
            "delivery_deadline": {
                "type": ["string", "null"],
                "description": 'Deadline the order must arrive by, as 24-hour "HH:MM". Null '
                "when the message states no delivery deadline.",
            },
        },
        "required": ["restaurant_name", "dish_names", "budget_limit", "delivery_deadline"],
        "additionalProperties": False,
    },
    "strict": True,
}

TARGETED_ORDER_SYSTEM_PROMPT = (
    "You classify a WhatsApp message asking EasyOrder to place an order from one named "
    "restaurant. Extract the restaurant name, the specific dish names requested, an "
    "optional budget limit in INR (only if the message says to confirm/check before "
    "placing when a budget is exceeded), and an optional delivery deadline. Never invent "
    "a restaurant, dish, budget, or deadline the message does not state — use null for "
    "budget_limit/delivery_deadline when absent."
)


class LLMTargetedOrderIntentParser:
    """Parses targeted-order prompts with a real LLM; falls back to the
    deterministic parser on any failure, mirroring LLMIntentParser."""

    def __init__(
        self,
        api_key: str,
        model: str,
        fallback: TargetedOrderIntentParser | None = None,
        client: AsyncOpenAI | None = None,
    ) -> None:
        self._client = client or AsyncOpenAI(api_key=api_key)
        self._model = model
        self._fallback = fallback or MockTargetedOrderIntentParser()

    async def parse(self, prompt: str) -> TargetedOrderIntent | None:
        try:
            return await self._parse_with_llm(prompt)
        except Exception:
            logger.warning(
                "llm_targeted_order_intent_parse_failed_falling_back_to_mock_parser",
                exc_info=True,
            )
            return await self._fallback.parse(prompt)

    async def _parse_with_llm(self, prompt: str) -> TargetedOrderIntent | None:
        response = await self._client.chat.completions.create(
            model=self._model,
            messages=[
                {"role": "system", "content": TARGETED_ORDER_SYSTEM_PROMPT},
                {"role": "user", "content": prompt},
            ],
            response_format={"type": "json_schema", "json_schema": TARGETED_ORDER_INTENT_SCHEMA},
        )
        content = response.choices[0].message.content
        if not content:
            raise ValueError("LLM returned no content")
        return _to_targeted_order_intent(json.loads(content))


def _to_targeted_order_intent(data: dict[str, Any]) -> TargetedOrderIntent | None:
    restaurant_name = str(data.get("restaurant_name") or "").strip()
    dish_names = [str(name).strip() for name in data.get("dish_names") or [] if str(name).strip()]
    if not restaurant_name:
        return None

    budget_limit = None
    if data.get("budget_limit") is not None:
        try:
            budget_limit = Decimal(str(data["budget_limit"])).quantize(Decimal("0.01"))
        except (InvalidOperation, TypeError):
            budget_limit = None

    deadline_minutes = None
    deadline_text = data.get("delivery_deadline")
    if deadline_text:
        match = re.match(r"^(\d{1,2}):(\d{2})$", str(deadline_text).strip())
        if match:
            deadline_minutes = int(match.group(1)) * 60 + int(match.group(2))

    return TargetedOrderIntent(
        restaurant_name=restaurant_name,
        dish_names=dish_names,
        budget_limit=budget_limit,
        delivery_deadline_minutes=deadline_minutes,
    )


def create_targeted_order_parser(
    *, mode: str, api_key: str, model: str
) -> TargetedOrderIntentParser:
    if mode == "openai":
        if not api_key:
            raise LLMIntentConfigurationError("OPENAI_API_KEY is required when LLM_MODE=openai")
        return LLMTargetedOrderIntentParser(api_key=api_key, model=model)
    return MockTargetedOrderIntentParser()
