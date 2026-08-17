"""EasyOrder agent orchestration for initializing group-order sessions."""

from __future__ import annotations

import asyncio
import logging
import re
from dataclasses import dataclass, field, replace
from decimal import Decimal
from typing import Any, Protocol

from langgraph.graph import END, StateGraph

from app.models.profile import UserProfile
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
from app.services.profile_builder import describe_applied_defaults, load_profile
from app.services.protocols import IAgentService, IDBAdapter, ISwiggyMcpClient

logger = logging.getLogger("easyorder.api")

WORKER_TIMEOUT_SECONDS = 2.5
# How far back the profile reads. Deep enough to be a real habit, shallow
# enough that deriving it live stays two cheap indexed reads.
PROFILE_HISTORY_LIMIT = 100
DEFAULT_LAT = 12.9716
DEFAULT_LNG = 77.5946


class AgentRejectedPromptError(ValueError):
    """Raised when input guardrails reject a prompt before parsing."""


@dataclass(frozen=True)
class RequestedItem:
    """One dish the message named, with the quantity it asked for.

    A group order is usually a list ("2 biryani, 1 mixed veg, 3 roti"), and
    every one of those is a cart row the host expects to see. Collapsing them
    into a single search string loses both the dishes and their counts.
    """

    name: str
    quantity: int


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
    # Dishes named with an explicit count. Empty when the prompt was vague
    # ("get biryani"), in which case the agent seeds a starter recommendation
    # for the group to edit instead of inventing quantities.
    requested_items: tuple[RequestedItem, ...] = ()
    # Field names the user actually stated, as opposed to ones carrying a
    # fallback. Without this the profile node cannot tell "under 3000" from the
    # 3000 the parser invented, and would overwrite a real instruction.
    specified: frozenset[str] = frozenset()


@dataclass
class EasyOrderState:
    """Mutable graph state passed between agent nodes."""

    message: IncomingMessage
    sanitized_prompt: str | None = None
    intent: ParsedIntent | None = None
    profile: UserProfile | None = None
    applied_defaults: list[str] = field(default_factory=list)
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


# Everything before the first "from/under/for" is the list of dishes; the rest
# is where to buy them and what to spend.
_ITEM_CLAUSE_STOP = re.compile(r"\b(?:from|under|for)\b")
_QUANTIFIED_ITEM = re.compile(r"^(?:get|order|need|want|send)?\s*(\d+)\s+(.+)$")


def extract_requested_items(prompt: str) -> tuple[RequestedItem, ...]:
    """Pull "2 chicken biryani, 1 mixed veg and 3 tandoori roti" apart.

    Only fragments carrying an explicit count become requested items. A vague
    prompt has none, and the caller falls back to a starter recommendation —
    better than turning "get biryani" into a row literally named "get biryani".
    """
    clause = prompt.lower()
    stop = _ITEM_CLAUSE_STOP.search(clause)
    if stop is not None:
        clause = clause[: stop.start()]

    items: list[RequestedItem] = []
    for fragment in re.split(r",|\band\b", clause):
        match = _QUANTIFIED_ITEM.match(fragment.strip())
        if match is None:
            continue
        name = match.group(2).strip()
        if not name:
            continue
        items.append(RequestedItem(name=name, quantity=max(1, min(99, int(match.group(1))))))
    return tuple(items)


class IntentParser(Protocol):
    """Interface for parsing a sanitized WhatsApp prompt into a ParsedIntent."""

    async def parse(self, prompt: str) -> ParsedIntent:
        """Extract budget, headcount, dietary preference, and search queries."""
        ...


class MockIntentParser:
    """Deterministic parser used in local mock mode and unit tests."""

    async def parse(self, prompt: str) -> ParsedIntent:
        normalized = prompt.replace("@EasyOrder", "").strip()
        specified: set[str] = set()

        stated_budget = self._extract_decimal(normalized, r"\bunder\s+(\d+(?:\.\d+)?)")
        if stated_budget is not None:
            specified.add("budget_limit")
        budget = stated_budget if stated_budget is not None else Decimal("3000")

        stated_head_count = self._extract_decimal(normalized, r"\bfor\s+(\d+)\b")
        if stated_head_count is not None:
            specified.add("head_count")
        head_count = int(stated_head_count if stated_head_count is not None else Decimal("4"))

        lowered = normalized.lower()
        dietary_preference = DietaryTag.ANY
        if "vegetarian" in lowered or re.search(r"\bveg\b", lowered):
            dietary_preference = DietaryTag.VEG
        elif "non-veg" in lowered or "chicken" in lowered:
            dietary_preference = DietaryTag.NON_VEG
        if dietary_preference != DietaryTag.ANY:
            specified.add("dietary_preference")

        return ParsedIntent(
            budget_limit=budget,
            head_count=max(1, min(head_count, 100)),
            dietary_preference=dietary_preference,
            food_query=self._extract_query(normalized, Vertical.FOOD) or "food",
            instamart_query=self._extract_query(normalized, Vertical.INSTAMART),
            requested_items=extract_requested_items(normalized),
            specified=frozenset(specified),
        )

    @staticmethod
    def _extract_decimal(prompt: str, pattern: str) -> Decimal | None:
        """Return the stated value, or None when the prompt didn't state one."""
        match = re.search(pattern, prompt, re.IGNORECASE)
        if not match:
            return None
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


@dataclass(frozen=True)
class TargetedOrderIntent:
    """Structured constraints extracted from a single-restaurant order prompt.

    A deliberately different shape from ParsedIntent: this describes one
    named restaurant and named dishes, not a multi-item group-session query.
    """

    restaurant_name: str
    dish_names: list[str]
    budget_limit: Decimal | None
    # Minutes since midnight (e.g. 20*60 for 8PM), or None when the prompt
    # never stated a delivery deadline.
    delivery_deadline_minutes: int | None


class TargetedOrderIntentParser(Protocol):
    """Interface for parsing a targeted single-restaurant order prompt."""

    async def parse(self, prompt: str) -> TargetedOrderIntent | None:
        """Extract restaurant name, dish names, budget limit, and delivery deadline."""
        ...


_TARGETED_ORDER_VERB = r"\b(?:order|get|need|want|send)\b"
_RESTAURANT_NAME_PATTERN = re.compile(
    r"\bfrom\s+([A-Za-z][A-Za-z0-9&' -]*?)"
    r"(?:\s+restaurant\b|\s*,|\s+and\b|\s+if\b|\s+it\b|\s*$)",
    re.IGNORECASE,
)
_DISH_NAMES_PATTERN = re.compile(
    _TARGETED_ORDER_VERB + r"\s+(.*?)\s+from\b",
    re.IGNORECASE,
)
_DISH_FILLER_PATTERN = re.compile(r"\bfor\s+(me|us|myself)\b", re.IGNORECASE)
_BUDGET_LIMIT_PATTERN = re.compile(
    r"budget\s+exceeds?\s+(?:inr\s*)?(\d+)",
    re.IGNORECASE,
)
_DELIVERY_DEADLINE_PATTERN = re.compile(
    r"\breach(?:es)?\s+by\s+(\d{1,2})\s*(am|pm)\b",
    re.IGNORECASE,
)


class MockTargetedOrderIntentParser:
    """Deterministic parser for single-restaurant order prompts."""

    async def parse(self, prompt: str) -> TargetedOrderIntent | None:
        restaurant_match = _RESTAURANT_NAME_PATTERN.search(prompt)
        if restaurant_match is None:
            return None
        restaurant_name = restaurant_match.group(1).strip()

        dish_names = self._extract_dish_names(prompt)
        if not restaurant_name and not dish_names:
            return None

        budget_match = _BUDGET_LIMIT_PATTERN.search(prompt)
        budget_limit = Decimal(budget_match.group(1)) if budget_match else None

        deadline_minutes = self._extract_deadline_minutes(prompt)

        return TargetedOrderIntent(
            restaurant_name=restaurant_name,
            dish_names=dish_names,
            budget_limit=budget_limit,
            delivery_deadline_minutes=deadline_minutes,
        )

    @staticmethod
    def _extract_dish_names(prompt: str) -> list[str]:
        match = _DISH_NAMES_PATTERN.search(prompt)
        if match is None:
            return []
        raw = _DISH_FILLER_PATTERN.sub("", match.group(1))
        parts = re.split(r"\s*,\s*|\s+and\s+", raw, flags=re.IGNORECASE)
        return [part.strip() for part in parts if part.strip()]

    @staticmethod
    def _extract_deadline_minutes(prompt: str) -> int | None:
        match = _DELIVERY_DEADLINE_PATTERN.search(prompt)
        if match is None:
            return None
        hour_12 = int(match.group(1)) % 12
        is_pm = match.group(2).lower() == "pm"
        hour_24 = hour_12 + (12 if is_pm else 0)
        return hour_24 * 60


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
                ("profile_defaults", self.apply_profile_defaults),
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
        return SessionInitResult(
            session=final_state.session,
            host_token=final_state.host_token,
            applied_defaults=final_state.applied_defaults,
            defaults_note=(
                describe_applied_defaults(final_state.profile, final_state.applied_defaults)
                if final_state.profile is not None
                else ""
            ),
        )

    async def apply_input_guardrails(self, state: EasyOrderState) -> EasyOrderState:
        state.sanitized_prompt = self.guardrails.sanitize(state.message.message_text)
        return state

    async def parse_intent(self, state: EasyOrderState) -> EasyOrderState:
        if state.sanitized_prompt is None:
            raise ValueError("sanitized prompt is required")
        state.intent = await self.parser.parse(state.sanitized_prompt)
        return state

    async def apply_profile_defaults(self, state: EasyOrderState) -> EasyOrderState:
        """Fill slots the user left unsaid with what they usually order.

        Three rules hold this node honest:

        1. It only ever writes to a field absent from ``intent.specified`` —
           an explicit instruction is never overwritten by a habit.
        2. Nothing is applied below ``MIN_OBSERVATIONS``; a default guessed
           from one order is worse than no default at all.
        3. Whatever it applies is recorded in ``state.applied_defaults`` so the
           reply can say so. A silent default the user cannot see is
           indistinguishable from a bug, and they cannot correct it.

        The profile is derived live from committed history, so it is current by
        construction — there is no cache to invalidate and an order placed a
        moment ago already counts. Failure here is never fatal: a profile is an
        improvement to the order, not a precondition for it.
        """
        if state.intent is None:
            raise ValueError("intent is required")

        try:
            profile = await load_profile(
                self.db, state.message.sender_id, limit=PROFILE_HISTORY_LIMIT
            )
        except Exception:
            logger.warning(
                "profile_build_failed",
                extra={"sender_id": state.message.sender_id},
                exc_info=True,
            )
            return state

        state.profile = profile
        if not profile.is_confident:
            return state

        applied: list[str] = []
        intent = state.intent
        updates: dict[str, Any] = {}

        if "budget_limit" not in intent.specified and profile.typical_budget is not None:
            updates["budget_limit"] = profile.typical_budget
            applied.append("budget_limit")
        if "head_count" not in intent.specified and profile.usual_headcount is not None:
            updates["head_count"] = profile.usual_headcount
            applied.append("head_count")
        if "dietary_preference" not in intent.specified and profile.dietary_tendency is not None:
            updates["dietary_preference"] = profile.dietary_tendency
            applied.append("dietary_preference")

        if updates:
            state.intent = replace(intent, **updates)
            state.applied_defaults = applied
            logger.info(
                "profile_defaults_applied",
                extra={"applied": applied, "observations": profile.observations},
            )
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

        state.cart_items = self._build_cart(state)
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

        # Only size the rows the user did not size themselves. Scaling an
        # explicit "3 tandoori roti" up to the headcount would silently reorder
        # the group's own decision.
        requested_names = {item.name.lower() for item in state.intent.requested_items}
        for item in state.cart_items:
            if requested_names and any(
                word in item.name.lower() for name in requested_names for word in name.split()
            ):
                continue
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

    def _build_cart(self, state: EasyOrderState) -> list[CartItem]:
        """One cart row per dish the message named, else a starter to edit.

        The old behaviour took the first usable search result and nothing else,
        so "2 chicken biryani, 1 mixed veg and 3 tandoori roti" produced a
        single row — the host saw one dish and had to rebuild the rest by hand.
        """
        if state.intent is None:
            raise ValueError("intent is required")

        usable = [
            result
            for result in state.food_results
            if not self._is_placeholder_result(result)
            and self._has_required_source_attribution(result, state)
        ]
        cart: list[CartItem] = []

        if state.intent.requested_items and usable:
            claimed: set[str] = set()
            missed: list[str] = []
            for requested in state.intent.requested_items:
                match = self._best_match(requested.name, usable, claimed)
                if match is None:
                    missed.append(requested.name)
                    continue
                claimed.add(str(match["item_id"]))
                item = self._cart_item_from_result(match, state.message.sender_id)
                item.quantity = requested.quantity
                cart.append(item)
            if missed:
                # Say what could not be found rather than silently dropping it —
                # a short cart with no explanation reads as a broken agent.
                state.warnings.append(
                    SessionWarning(
                        code="ITEM_NOT_FOUND",
                        message=(
                            "Couldn't find " + ", ".join(missed) + " nearby. "
                            "Add it on the canvas or try a different name."
                        ),
                        vertical=Vertical.FOOD,
                    )
                )

        if not cart:
            # Reuse the already-filtered list: `_has_required_source_attribution`
            # records a warning per rejected item, so calling it twice on the
            # same result would report the same problem twice.
            cart = [
                self._cart_item_from_result(result, state.message.sender_id)
                for result in usable[:1]
            ]

        cart += [
            self._cart_item_from_result(result, state.message.sender_id)
            for result in self._starter_recommendations(state.instamart_results)
            if self._has_required_source_attribution(result, state)
        ]
        return cart

    @staticmethod
    def _best_match(
        name: str,
        results: list[dict[str, Any]],
        claimed: set[str],
    ) -> dict[str, Any] | None:
        """Pick the search result whose name shares the most words with the request."""
        wanted = {word for word in re.findall(r"[a-z]+", name.lower()) if len(word) > 2}
        best: tuple[int, dict[str, Any]] | None = None
        for result in results:
            if str(result["item_id"]) in claimed:
                continue
            tokens = {
                word for word in re.findall(r"[a-z]+", str(result["name"]).lower()) if len(word) > 2
            }
            score = len(wanted & tokens)
            if score and (best is None or score > best[0]):
                best = (score, result)
        return best[1] if best else None

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
