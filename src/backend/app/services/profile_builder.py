"""Deterministic derivation of a UserProfile from committed order history.

Pure functions over rows already in EasyOrder's database. No LLM call, no
network, no randomness — percentiles and frequencies are exact and cheap in
Python, and a model asked to compute them would be subtly wrong in ways no test
catches. When the LLM layer arrives it belongs on the parts that are actually
language (cuisine affinity, complaint themes), not on this.

Committed history only. An order awaiting confirmation, one scheduled for
later, a cancelled order, or a cart still being planned are all statements of
intent, not evidence of what this user does — counting them would teach the
profile from orders that never happened.
"""

from __future__ import annotations

from collections import Counter
from datetime import datetime
from decimal import ROUND_HALF_UP, Decimal

from app.models.order import Order
from app.models.profile import (
    DIETARY_MAJORITY,
    FAVOURITES_KEPT,
    RestaurantAffinity,
    UserProfile,
)
from app.models.session import DietaryTag, Session, SessionStatus
from app.models.spend import SPENT_ORDER_STATUSES
from app.services.protocols import IDBAdapter

WEEKDAYS = ("Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday")

#: Budgets are rounded to this so a learned default reads like a number a human
#: would have typed. "Your usual 1,800" lands; "your usual 1,777.50" reads as a
#: machine showing its working.
BUDGET_ROUNDING = Decimal("50")


async def load_profile(db: IDBAdapter, wa_id: str, *, limit: int = 100) -> UserProfile:
    """Read a user's history and summarize it.

    Derived on every call rather than cached: the history is two indexed reads,
    and a profile that is always recomputed is a profile that can never be
    stale. An order placed a second ago already counts.
    """
    orders = await db.list_orders_for_host(wa_id, limit=limit)
    sessions = await db.list_sessions_for_host(wa_id, limit=limit)
    return build_profile(wa_id, orders, sessions)


def build_profile(
    wa_id: str,
    orders: list[Order],
    sessions: list[Session],
) -> UserProfile:
    """Summarize one user's committed orders into a profile.

    Both lists are the caller's full available history; filtering to committed
    records happens here so the rule lives in one place.
    """
    committed_orders = [order for order in orders if order.status in SPENT_ORDER_STATUSES]
    committed_sessions = [s for s in sessions if s.status == SessionStatus.ORDERED]
    observations = len(committed_orders) + len(committed_sessions)

    if observations == 0:
        return UserProfile(wa_id=wa_id)

    totals = [order.total for order in committed_orders]
    totals += [_session_total(session) for session in committed_sessions]
    totals = [total for total in totals if total > 0]

    timestamps = [order.created_at for order in committed_orders]
    timestamps += [session.created_at for session in committed_sessions]

    typical_budget = _typical_budget(totals)
    return UserProfile(
        wa_id=wa_id,
        observations=observations,
        typical_budget=typical_budget,
        budget_ceiling=_budget_ceiling(totals, typical_budget),
        usual_headcount=_usual_headcount(committed_sessions),
        dietary_tendency=_dietary_tendency(committed_sessions),
        favourites=_favourites(committed_orders, committed_sessions),
        busiest_weekday=_modal_weekday(timestamps),
        busiest_hour=_modal_hour(timestamps),
        last_ordered_at=max(timestamps) if timestamps else None,
    )


def _session_total(session: Session) -> Decimal:
    return sum((item.price * item.quantity for item in session.cart_items), Decimal("0"))


def _percentile(values: list[Decimal], fraction: float) -> Decimal | None:
    """Nearest-rank percentile. Exact, and stable for the tiny n we have here."""
    if not values:
        return None
    ordered = sorted(values)
    index = min(len(ordered) - 1, max(0, round(fraction * (len(ordered) - 1))))
    return ordered[index]


def _typical_budget(totals: list[Decimal]) -> Decimal | None:
    """Median spend, rounded up to a human-looking number.

    Rounded *up* deliberately: a budget default that lands under what the user
    normally spends filters out the orders they'd actually want.
    """
    median = _percentile(totals, 0.5)
    if median is None:
        return None
    rounded = (median / BUDGET_ROUNDING).to_integral_value(rounding=ROUND_HALF_UP)
    rounded = rounded * BUDGET_ROUNDING
    return max(rounded, median).quantize(Decimal("0.01"))


def _budget_ceiling(totals: list[Decimal], typical: Decimal | None) -> Decimal | None:
    """The high end of what this user spends.

    Never reported below `typical`: the median is rounded up to a human number,
    so on a tight spread the raw p90 can land under it, and a "ceiling" lower
    than the "usual" is nonsense to whoever reads it.
    """
    ceiling = _percentile(totals, 0.9)
    if ceiling is None:
        return None
    if typical is not None:
        ceiling = max(ceiling, typical)
    return ceiling.quantize(Decimal("0.01"))


def _usual_headcount(sessions: list[Session]) -> int | None:
    """Median headcount across group sessions.

    Targeted orders carry no headcount — they are one person ordering for
    themselves — so they are excluded rather than counted as one, which would
    drag the median down for someone who mostly hosts.
    """
    counts = [session.head_count for session in sessions if session.head_count > 0]
    if not counts:
        return None
    counts.sort()
    return counts[len(counts) // 2]


def _dietary_tendency(sessions: list[Session]) -> DietaryTag | None:
    """The user's dietary preference, only when it is a clear majority."""
    stated = [
        session.dietary_preference
        for session in sessions
        if session.dietary_preference != DietaryTag.ANY
    ]
    if len(stated) < 2:
        return None
    tag, count = Counter(stated).most_common(1)[0]
    if count / len(sessions) < DIETARY_MAJORITY:
        return None
    return tag


def _favourites(orders: list[Order], sessions: list[Session]) -> list[RestaurantAffinity]:
    """Restaurants ordered from most often, ties broken by recency."""
    counts: Counter[str] = Counter()
    last_seen: dict[str, datetime] = {}

    def record(name: str | None, when: datetime) -> None:
        if not name:
            return
        counts[name] += 1
        if name not in last_seen or when > last_seen[name]:
            last_seen[name] = when

    for order in orders:
        record(order.restaurant_name, order.created_at)
    for session in sessions:
        # One credit per restaurant per session: a session with six items from
        # one place is one visit, not six.
        for name in {item.restaurant_name for item in session.cart_items if item.restaurant_name}:
            record(name, session.created_at)

    ranked = sorted(counts.items(), key=lambda pair: (-pair[1], -last_seen[pair[0]].timestamp()))
    return [
        RestaurantAffinity(
            restaurant_name=name,
            order_count=count,
            last_ordered_at=last_seen[name],
        )
        for name, count in ranked[:FAVOURITES_KEPT]
    ]


def _modal_weekday(timestamps: list[datetime]) -> str | None:
    if not timestamps:
        return None
    return WEEKDAYS[Counter(ts.weekday() for ts in timestamps).most_common(1)[0][0]]


def _modal_hour(timestamps: list[datetime]) -> int | None:
    if not timestamps:
        return None
    return Counter(ts.hour for ts in timestamps).most_common(1)[0][0]


def describe_applied_defaults(profile: UserProfile, applied: list[str]) -> str:
    """One line naming what the profile filled in, for the WhatsApp reply.

    A default the user cannot see is indistinguishable from a bug, and they
    cannot correct what they were never told about — so anything applied here
    is always said out loud, with how to override it.
    """
    if not applied:
        return ""
    parts: list[str] = []
    if "budget_limit" in applied and profile.typical_budget is not None:
        parts.append(f"your usual budget of INR {profile.typical_budget:.0f}")
    if "head_count" in applied and profile.usual_headcount is not None:
        parts.append(f"your usual {profile.usual_headcount} people")
    if "dietary_preference" in applied and profile.dietary_tendency is not None:
        parts.append(f"your usual {profile.dietary_tendency} preference")
    if not parts:
        return ""
    joined = parts[0] if len(parts) == 1 else ", ".join(parts[:-1]) + f" and {parts[-1]}"
    return (
        f"You didn't say, so I used {joined} "
        f"(from your last {profile.observations} orders). "
        "Say it in your message to override."
    )
