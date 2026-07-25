"""EasyOrder agent orchestration for initializing group-order sessions."""

from __future__ import annotations

import asyncio
import logging
import re
from dataclasses import dataclass, field
from decimal import Decimal
from typing import Any, Protocol

from langgraph.graph import END, StateGraph

from app.models.session import (
    CartItem,
    DietaryTag,
    Session,
    SessionCreate,
    SessionInitResult,
    SessionStatus,
    SessionWarning,
    Vertical,
    generate_session_tokens,
)
from app.models.whatsapp import IncomingMessage
from app.observability import AGENT_ERRORS_TOTAL
from app.services.protocols import IAgentService, IDBAdapter, ISwiggyMcpClient

logger = logging.getLogger("easyorder.api")

WORKER_TIMEOUT_SECONDS = 2.5
DEFAULT_LAT = 12.9716
DEFAULT_LNG = 77.5946


class AgentRejectedPromptError(ValueError):
    """Raised when input guardrails reject a prompt before parsing."""


@dataclass(frozen=True)
class ParsedIntent:
    """Structured order constraints extracted from a WhatsApp prompt."""

    budget_limit: Decimal
    head_count: int
    dietary_preference: DietaryTag
    food_query: str
    # None when the prompt never asked for Instamart items; the vertical is
    # skipped entirely so the seeded cart only contains what was requested.
    instamart_query: str | None


@dataclass
class EasyOrderState:
    """Mutable graph state passed between agent nodes."""

    message: IncomingMessage
    sanitized_prompt: str | None = None
    intent: ParsedIntent | None = None
    food_results: list[dict[str, Any]] = field(default_factory=list)
    instamart_results: list[dict[str, Any]] = field(default_factory=list)
    degraded_verticals: list[Vertical] = field(default_factory=list)
    warnings: list[SessionWarning] = field(default_factory=list)
    cart_items: list[CartItem] = field(default_factory=list)
    budget_warning: bool = False
    session: Session | None = None
    host_token: str | None = None
    status: SessionStatus = SessionStatus.INITIALIZING
    errors: list[str] = field(default_factory=list)


class AgentNode(Protocol):
    """Node callable used by the lightweight EasyOrder graph."""

    async def __call__(self, state: EasyOrderState) -> EasyOrderState:
        ...


class EasyOrderGraph:
    """LangGraph runner with explicit node names for debuggability."""

    def __init__(self, nodes: list[tuple[str, AgentNode]]) -> None:
        self.nodes = nodes
        self._compiled: Any | None = None

    def compile(self) -> EasyOrderGraph:
        if not self.nodes:
            raise ValueError("EasyOrder graph requires at least one node")
        graph = StateGraph(EasyOrderState)
        for name, node in self.nodes:
            graph.add_node(name, self._wrap_node(name, node))

        graph.set_entry_point(self.nodes[0][0])
        for (name, _node), (next_name, _next_node) in zip(self.nodes, self.nodes[1:], strict=False):
            graph.add_edge(name, next_name)
        graph.add_edge(self.nodes[-1][0], END)
        self._compiled = graph.compile()
        return self

    async def invoke(self, state: EasyOrderState) -> EasyOrderState:
        if self._compiled is None:
            self.compile()
        result = await self._compiled.ainvoke(state)
        if isinstance(result, EasyOrderState):
            return result
        return EasyOrderState(**result)

    @staticmethod
    def _wrap_node(name: str, node: AgentNode) -> AgentNode:
        async def wrapped(state: EasyOrderState) -> EasyOrderState:
            if state.errors:
                return state
            try:
                return await node(state)
            except AgentRejectedPromptError:
                raise
            except Exception as error:
                state.errors.append(f"{name}: {error.__class__.__name__}")
                state.status = SessionStatus.DEGRADED
                AGENT_ERRORS_TOTAL.labels(node=name).inc()
                return state

        return wrapped


class InputGuardrails:
    """Blocks prompt injection and masks obvious PII before parsing."""

    injection_patterns = [
        re.compile(pattern, re.IGNORECASE)
        for pattern in (
            r"ignore\s+(all\s+)?previous\s+instructions",
            r"system\s+prompt",
            r"developer\s+message",
            r"jailbreak",
        )
    ]
    pii_patterns = [
        re.compile(r"\b[\w.+-]+@[\w-]+\.[\w.-]+\b"),
        re.compile(r"\b(?:\+?91[-\s]?)?[6-9]\d{9}\b"),
        re.compile(r"\b(?:\d[ -]*?){13,16}\b"),
    ]

    def sanitize(self, prompt: str) -> str:
        if any(pattern.search(prompt) for pattern in self.injection_patterns):
            raise AgentRejectedPromptError("Prompt failed input safety checks")

        sanitized = prompt
        for pattern in self.pii_patterns:
            sanitized = pattern.sub("[redacted]", sanitized)
        return sanitized.strip()


class IntentParser(Protocol):
    """Interface for parsing a sanitized WhatsApp prompt into a ParsedIntent."""

    async def parse(self, prompt: str) -> ParsedIntent:
        """Extract budget, headcount, dietary preference, and search queries."""
        ...


class MockIntentParser:
    """Deterministic parser used in local mock mode and unit tests."""

    async def parse(self, prompt: str) -> ParsedIntent:
        normalized = prompt.replace("@EasyOrder", "").strip()
        budget = self._extract_decimal(normalized, r"\bunder\s+(\d+(?:\.\d+)?)", Decimal("3000"))
        head_count = int(self._extract_decimal(normalized, r"\bfor\s+(\d+)\b", Decimal("4")))
        lowered = normalized.lower()
        dietary_preference = DietaryTag.ANY
        if "vegetarian" in lowered or re.search(r"\bveg\b", lowered):
            dietary_preference = DietaryTag.VEG
        elif "non-veg" in lowered or "chicken" in lowered:
            dietary_preference = DietaryTag.NON_VEG

        return ParsedIntent(
            budget_limit=budget,
            head_count=max(1, min(head_count, 100)),
            dietary_preference=dietary_preference,
            food_query=self._extract_query(normalized, Vertical.FOOD) or "food",
            instamart_query=self._extract_query(normalized, Vertical.INSTAMART),
        )

    @staticmethod
    def _extract_decimal(prompt: str, pattern: str, default: Decimal) -> Decimal:
        match = re.search(pattern, prompt, re.IGNORECASE)
        if not match:
            return default
        return Decimal(match.group(1)).quantize(Decimal("0.01"))

    @staticmethod
    def _extract_query(prompt: str, vertical: Vertical) -> str | None:
        lowered = prompt.lower()
        if vertical == Vertical.INSTAMART:
            keywords = ["drinks", "cold drinks", "plates", "ice cream", "water", "dessert"]
            return " ".join(keyword for keyword in keywords if keyword in lowered) or None
        stopwords = {"get", "for", "under", "people", "person", "and", "with"}
        words = re.findall(r"[a-zA-Z][a-zA-Z-]*", lowered)
        return " ".join(word for word in words if word not in stopwords) or None


class EasyOrderAgentService(IAgentService):
    """Initializes EasyOrder sessions from tagged WhatsApp messages."""

    def __init__(
        self,
        db: IDBAdapter,
        swiggy_client: ISwiggyMcpClient,
        parser: IntentParser | None = None,
        guardrails: InputGuardrails | None = None,
        worker_timeout_seconds: float = WORKER_TIMEOUT_SECONDS,
    ) -> None:
        self.db = db
        self.swiggy_client = swiggy_client
        self.parser = parser or MockIntentParser()
        self.guardrails = guardrails or InputGuardrails()
        self.worker_timeout_seconds = worker_timeout_seconds
        self.handled_messages: list[IncomingMessage] = []
        self.graph = self.build_graph().compile()

    def build_graph(self) -> EasyOrderGraph:
        return EasyOrderGraph(
            [
                ("input_guardrails", self.apply_input_guardrails),
                ("intent_parser", self.parse_intent),
                ("swiggy_workers", self.run_workers),
                ("output_guardrails", self.apply_output_guardrails),
                ("persistence", self.persist_session),
            ]
        )

    async def handle_tagged_message(self, message: IncomingMessage) -> Session:
        return (await self.initialize_tagged_message(message)).session

    async def initialize_tagged_message(self, message: IncomingMessage) -> SessionInitResult:
        self.handled_messages.append(message)
        final_state = await self.graph.invoke(EasyOrderState(message=message))
        if final_state.session is None and final_state.errors:
            final_state.session = await self.persist_error_session(final_state)
        if final_state.session is None:
            raise RuntimeError("Agent graph finished without a persisted session")
        if final_state.host_token is None:
            raise RuntimeError("Agent graph finished without host token material")
        return SessionInitResult(session=final_state.session, host_token=final_state.host_token)

    async def apply_input_guardrails(self, state: EasyOrderState) -> EasyOrderState:
        state.sanitized_prompt = self.guardrails.sanitize(state.message.message_text)
        return state

    async def parse_intent(self, state: EasyOrderState) -> EasyOrderState:
        if state.sanitized_prompt is None:
            raise ValueError("sanitized prompt is required")
        state.intent = await self.parser.parse(state.sanitized_prompt)
        return state

    async def run_workers(self, state: EasyOrderState) -> EasyOrderState:
        if state.intent is None:
            raise ValueError("intent is required")

        food_task = self._run_worker(
            Vertical.FOOD,
            self.swiggy_client.search_restaurants(
                DEFAULT_LAT,
                DEFAULT_LNG,
                state.intent.food_query,
            ),
        )
        if state.intent.instamart_query is None:
            food_result = await food_task
            self._merge_worker_result(state, Vertical.FOOD, food_result)
            return state

        instamart_task = self._run_worker(
            Vertical.INSTAMART,
            self.swiggy_client.search_instamart(
                DEFAULT_LAT,
                DEFAULT_LNG,
                state.intent.instamart_query,
            ),
        )
        food_result, instamart_result = await asyncio.gather(food_task, instamart_task)
        self._merge_worker_result(state, Vertical.FOOD, food_result)
        self._merge_worker_result(state, Vertical.INSTAMART, instamart_result)
        return state

    async def _run_worker(
        self,
        vertical: Vertical,
        query: object,
    ) -> tuple[list[dict[str, Any]], SessionWarning | None]:
        try:
            results = await asyncio.wait_for(query, timeout=self.worker_timeout_seconds)
            return results, None
        except TimeoutError:
            return [], SessionWarning(
                code="VERTICAL_TIMEOUT",
                message=f"{self._vertical_label(vertical)} search timed out. Add items manually.",
                vertical=vertical,
            )
        except Exception:
            logger.warning(
                "swiggy_worker_failed",
                extra={"vertical": str(vertical)},
                exc_info=True,
            )
            return [], SessionWarning(
                code="VERTICAL_FAILED",
                message=(
                    f"{self._vertical_label(vertical)} search is temporarily "
                    "unavailable. Add items manually."
                ),
                vertical=vertical,
            )

    def _merge_worker_result(
        self,
        state: EasyOrderState,
        vertical: Vertical,
        result: tuple[list[dict[str, Any]], SessionWarning | None],
    ) -> None:
        items, warning = result
        if vertical == Vertical.FOOD:
            state.food_results = items
        else:
            state.instamart_results = items
        if warning is not None:
            state.degraded_verticals.append(vertical)
            state.warnings.append(warning)

    async def apply_output_guardrails(self, state: EasyOrderState) -> EasyOrderState:
        if state.intent is None:
            raise ValueError("intent is required")

        recommendations = [
            *self._starter_recommendations(state.food_results),
            *self._starter_recommendations(state.instamart_results),
        ]
        state.cart_items = [
            self._cart_item_from_result(result, state.message.sender_id)
            for result in recommendations
            if self._has_required_source_attribution(result, state)
        ]
        self._apply_quantity_budget(state)
        self._apply_dietary_warning(state)
        if state.degraded_verticals:
            state.status = SessionStatus.DEGRADED
        else:
            state.status = SessionStatus.ACTIVE
        return state

    async def persist_session(self, state: EasyOrderState) -> EasyOrderState:
        if state.intent is None:
            raise ValueError("intent is required")

        tokens = generate_session_tokens()
        session = SessionCreate(
            whatsapp_group_id=state.message.phone_number_id,
            host_phone=state.message.sender_id,
            budget_limit=state.intent.budget_limit,
            head_count=state.intent.head_count,
            dietary_preference=state.intent.dietary_preference,
            status=state.status,
            budget_warning=state.budget_warning,
            degraded_verticals=state.degraded_verticals,
            warnings=state.warnings,
        )
        state.session = await self.db.create_session(
            session,
            host_token_hash=tokens.host_token_hash,
            guest_token=tokens.guest_token,
            cart_items=state.cart_items,
        )
        state.host_token = tokens.host_token
        return state

    async def persist_error_session(self, state: EasyOrderState) -> Session:
        tokens = generate_session_tokens()
        session = SessionCreate(
            whatsapp_group_id=state.message.phone_number_id,
            host_phone=state.message.sender_id,
            status=SessionStatus.DEGRADED,
            warnings=[
                *state.warnings,
                SessionWarning(
                    code="AGENT_ERROR",
                    message="Agent initialization degraded before recommendations were complete.",
                ),
            ],
        )
        state.host_token = tokens.host_token
        return await self.db.create_session(
            session,
            host_token_hash=tokens.host_token_hash,
            guest_token=tokens.guest_token,
            cart_items=state.cart_items,
        )

    def _apply_quantity_budget(self, state: EasyOrderState) -> None:
        if state.intent is None:
            raise ValueError("intent is required")

        for item in state.cart_items:
            if item.vertical == Vertical.FOOD:
                item.quantity = min(99, max(1, state.intent.head_count))
            else:
                item.quantity = min(99, max(1, (state.intent.head_count + 1) // 2))

        total = sum((item.price * item.quantity for item in state.cart_items), Decimal("0.00"))
        if total > state.intent.budget_limit:
            state.budget_warning = True
            state.warnings.append(
                SessionWarning(
                    code="BUDGET_EXCEEDED",
                    message=(
                        "Cart total exceeds budget by INR "
                        f"{total - state.intent.budget_limit}."
                    ),
                )
            )

    def _apply_dietary_warning(self, state: EasyOrderState) -> None:
        if state.intent is None:
            raise ValueError("intent is required")

        if state.intent.dietary_preference != DietaryTag.VEG:
            return
        for item in state.cart_items:
            if item.dietary_tag == DietaryTag.NON_VEG:
                state.warnings.append(
                    SessionWarning(
                        code="DIETARY_MISMATCH",
                        message=f"Non-veg item '{item.name}' appears in a vegetarian session.",
                        vertical=Vertical(item.vertical),
                        item_id=item.item_id,
                    )
                )

    @staticmethod
    def _starter_recommendations(results: list[dict[str, Any]]) -> list[dict[str, Any]]:
        usable = [
            result
            for result in results
            if not EasyOrderAgentService._is_placeholder_result(result)
        ]
        return usable[:1]

    @staticmethod
    def _cart_item_from_result(result: dict[str, Any], added_by: str) -> CartItem:
        return CartItem(
            item_id=str(result["item_id"]),
            name=str(result["name"]),
            quantity=1,
            price=Decimal(str(result["price"])),
            added_by=added_by,
            dietary_tag=DietaryTag(str(result.get("dietary_tag", DietaryTag.ANY))),
            vertical=Vertical(str(result["vertical"])),
            restaurant_id=result.get("restaurant_id"),
            restaurant_name=result.get("restaurant_name"),
            brand_name=result.get("brand_name"),
            source_label=result.get("source_label"),
        )

    @staticmethod
    def _has_required_source_attribution(
        result: dict[str, Any],
        state: EasyOrderState,
    ) -> bool:
        vertical = Vertical(str(result["vertical"]))
        if vertical == Vertical.FOOD:
            has_source = bool(result.get("restaurant_id") and result.get("restaurant_name"))
        else:
            has_source = bool(result.get("source_label"))
        if has_source:
            return True

        state.warnings.append(
            SessionWarning(
                code="SOURCE_ATTRIBUTION_MISSING",
                message=(
                    f"{EasyOrderAgentService._vertical_label(vertical)} item "
                    f"'{result.get('name', result.get('item_id', 'unknown'))}' "
                    "was skipped because source attribution was missing."
                ),
                vertical=vertical,
                item_id=str(result.get("item_id", "")) or None,
            )
        )
        return False

    @staticmethod
    def _is_placeholder_result(result: dict[str, Any]) -> bool:
        name = str(result.get("name", "")).lower()
        return "mock" in name or "placeholder" in name

    @staticmethod
    def _vertical_label(vertical: Vertical) -> str:
        return "Food" if vertical == Vertical.FOOD else "Instamart"
