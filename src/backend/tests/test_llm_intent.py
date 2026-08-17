import asyncio
import json
from decimal import Decimal

import pytest

from app.models.session import DietaryTag
from app.services.agent import MockIntentParser
from app.services.llm_intent import (
    LLMIntentConfigurationError,
    LLMIntentParser,
    create_intent_parser,
)


def run(coro):
    return asyncio.run(coro)


class FakeMessage:
    def __init__(self, content: str) -> None:
        self.content = content


class FakeChoice:
    def __init__(self, content: str) -> None:
        self.message = FakeMessage(content)


class FakeResponse:
    def __init__(self, content: str) -> None:
        self.choices = [FakeChoice(content)]


class FakeCompletions:
    def __init__(self, content: str | None = None, error: Exception | None = None) -> None:
        self.content = content
        self.error = error
        self.calls: list[dict] = []

    async def create(self, **kwargs):
        self.calls.append(kwargs)
        if self.error is not None:
            raise self.error
        return FakeResponse(self.content)


class FakeChat:
    def __init__(self, completions: FakeCompletions) -> None:
        self.completions = completions


class FakeOpenAIClient:
    def __init__(self, content: str | None = None, error: Exception | None = None) -> None:
        self.chat = FakeChat(FakeCompletions(content, error))


def test_llm_intent_parser_maps_valid_llm_response() -> None:
    payload = json.dumps(
        {
            "budget_limit": 2500,
            "head_count": 6,
            "dietary_preference": "VEG",
            "food_query": "paneer rolls",
            "wants_instamart": True,
            "instamart_query": "cold drinks",
        }
    )
    client = FakeOpenAIClient(content=payload)
    parser = LLMIntentParser(api_key="test-key", model="gpt-4o-mini", client=client)

    intent = run(parser.parse("get paneer rolls for 6 under 2500 and some cold drinks"))

    assert intent.budget_limit == Decimal("2500.00")
    assert intent.head_count == 6
    assert intent.dietary_preference == DietaryTag.VEG
    assert intent.food_query == "paneer rolls"
    assert intent.instamart_query == "cold drinks"
    assert client.chat.completions.calls[0]["model"] == "gpt-4o-mini"


def test_llm_intent_parser_clears_instamart_query_when_not_wanted() -> None:
    payload = json.dumps(
        {
            "budget_limit": 1000,
            "head_count": 2,
            "dietary_preference": "ANY",
            "food_query": "biryani",
            "wants_instamart": False,
            "instamart_query": "",
        }
    )
    client = FakeOpenAIClient(content=payload)
    parser = LLMIntentParser(api_key="test-key", model="gpt-4o-mini", client=client)

    intent = run(parser.parse("get biryani for 2 under 1000"))

    assert intent.instamart_query is None


def test_llm_intent_parser_clamps_head_count_to_valid_range() -> None:
    payload = json.dumps(
        {
            "budget_limit": 500,
            "head_count": 500,
            "dietary_preference": "ANY",
            "food_query": "snacks",
            "wants_instamart": False,
            "instamart_query": "",
        }
    )
    client = FakeOpenAIClient(content=payload)
    parser = LLMIntentParser(api_key="test-key", model="gpt-4o-mini", client=client)

    intent = run(parser.parse("snacks for the whole office"))

    assert intent.head_count == 100


def test_llm_intent_parser_falls_back_to_mock_parser_on_api_failure() -> None:
    client = FakeOpenAIClient(error=RuntimeError("rate limited"))
    parser = LLMIntentParser(api_key="test-key", model="gpt-4o-mini", client=client)

    intent = run(parser.parse("get biryani for 4 under 2000"))

    expected = run(MockIntentParser().parse("get biryani for 4 under 2000"))
    assert intent == expected


def test_llm_intent_parser_falls_back_to_mock_parser_on_malformed_response() -> None:
    client = FakeOpenAIClient(content="not json")
    parser = LLMIntentParser(api_key="test-key", model="gpt-4o-mini", client=client)

    intent = run(parser.parse("get biryani for 4 under 2000"))

    expected = run(MockIntentParser().parse("get biryani for 4 under 2000"))
    assert intent == expected


def test_create_intent_parser_factory() -> None:
    assert isinstance(
        create_intent_parser(mode="mock", api_key="", model="gpt-4o-mini"), MockIntentParser
    )

    with pytest.raises(LLMIntentConfigurationError):
        create_intent_parser(mode="openai", api_key="", model="gpt-4o-mini")

    parser = create_intent_parser(mode="openai", api_key="test-key", model="gpt-4o-mini")
    assert isinstance(parser, LLMIntentParser)


def test_llm_intent_parser_treats_null_fields_as_not_stated() -> None:
    # The model reports absence by omitting the value, not by a separate
    # boolean it can get out of sync with the value itself.
    payload = json.dumps(
        {
            "budget_limit": None,
            "head_count": None,
            "dietary_preference": "ANY",
            "food_query": "biryani",
            "wants_instamart": False,
            "instamart_query": "",
        }
    )
    parser = LLMIntentParser(
        api_key="test-key", model="gpt-4o-mini", client=FakeOpenAIClient(content=payload)
    )

    intent = run(parser.parse("get biryani"))

    assert intent.budget_limit == Decimal("3000.00")
    assert intent.head_count == 4
    assert "budget_limit" not in intent.specified
    assert "head_count" not in intent.specified


def test_llm_intent_parser_marks_a_stated_head_count_even_when_phrased_unusually() -> None:
    # This is the live bug: the model can extract the right number while
    # getting a *separate* self-report flag wrong. With no second flag to
    # desync, "specified" now follows directly from whether the field is
    # null — there is nothing left for the model to contradict.
    payload = json.dumps(
        {
            "budget_limit": None,
            "head_count": 4,
            "dietary_preference": "ANY",
            "food_query": "biryani",
            "wants_instamart": False,
            "instamart_query": "",
        }
    )
    parser = LLMIntentParser(
        api_key="test-key", model="gpt-4o-mini", client=FakeOpenAIClient(content=payload)
    )

    intent = run(parser.parse("get biryani for 4 under 2000"))

    assert intent.head_count == 4
    assert "head_count" in intent.specified


def test_llm_intent_parser_recognizes_budget_phrasing_a_fixed_regex_would_miss() -> None:
    # "budget of 2000" never matched \\bunder\\s+\\d+ under the old
    # regex-union design. Presence now comes from the field itself, so any
    # phrasing the model can extract a number from is covered by
    # construction — no phrase list to maintain.
    payload = json.dumps(
        {
            "budget_limit": 2000,
            "head_count": None,
            "dietary_preference": "ANY",
            "food_query": "biryani",
            "wants_instamart": False,
            "instamart_query": "",
        }
    )
    parser = LLMIntentParser(
        api_key="test-key", model="gpt-4o-mini", client=FakeOpenAIClient(content=payload)
    )

    intent = run(parser.parse("Order biryani with a budget of 2000."))

    assert intent.budget_limit == Decimal("2000.00")
    assert "budget_limit" in intent.specified


def test_llm_intent_parser_prefers_the_regex_item_list_when_the_message_matches_it() -> None:
    # The message matches the explicit "N item[, N item]*" grammar, so the
    # deterministic extractor's result is used outright — even though the
    # fake LLM response below returns a different (wrong) item list. Proves
    # the override, not just that the correct answer can appear by chance.
    payload = json.dumps(
        {
            "budget_limit": 2000,
            "head_count": None,
            "dietary_preference": "ANY",
            "food_query": "biryani",
            "items": [{"name": "chicken biryani", "quantity": 6}],  # deliberately wrong
            "wants_instamart": False,
            "instamart_query": "",
        }
    )
    parser = LLMIntentParser(
        api_key="test-key", model="gpt-4o-mini", client=FakeOpenAIClient(content=payload)
    )

    intent = run(
        parser.parse(
            "2 chicken biryani, 1 mixed veg and 3 tandoori roti from the best restaurant under 2000"
        )
    )

    items = {item.name: item.quantity for item in intent.requested_items}
    assert items == {"chicken biryani": 2, "mixed veg": 1, "tandoori roti": 3}


def test_llm_intent_parser_falls_back_to_llm_items_for_free_form_phrasing() -> None:
    # No comma/and list with explicit counts here, so the regex extractor
    # finds nothing and the model's item list is used as-is.
    payload = json.dumps(
        {
            "budget_limit": None,
            "head_count": None,
            "dietary_preference": "ANY",
            "food_query": "biryani",
            "items": [{"name": "chicken biryani", "quantity": 2}],
            "wants_instamart": False,
            "instamart_query": "",
        }
    )
    parser = LLMIntentParser(
        api_key="test-key", model="gpt-4o-mini", client=FakeOpenAIClient(content=payload)
    )

    intent = run(parser.parse("get me two chicken biryanis"))

    items = {item.name: item.quantity for item in intent.requested_items}
    assert items == {"chicken biryani": 2}
