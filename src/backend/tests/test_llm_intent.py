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
