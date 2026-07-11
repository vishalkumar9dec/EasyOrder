"""Order-history answers from EasyOrder's own durable session data (task 10.6).

Phase 1 scope: "what was my last order?" in the dedicated business chat is
answered from the sender's most recent EasyOrder session — date, items,
total, status, and a fresh guest short link. Live Swiggy order/delivery
scopes remain deferred; replies say so instead of guessing.

Privacy: replies go to the session's own host wa_id and carry the guest
short link only. Host tokens are stored hashed and can never be rebuilt
into a link here — by design.
"""

from __future__ import annotations

from decimal import Decimal

from app.models.session import Session, SessionStatus
from app.services.protocols import IDBAdapter, IShortLinkService

NO_HISTORY_REPLY = (
    "I don't have any orders for you yet. Tell me what to order, for "
    "example: get biryani for 4 under 2000."
)

_STATUS_PHRASES = {
    str(SessionStatus.INITIALIZING): "is still being set up",
    str(SessionStatus.ACTIVE): "is still being planned",
    str(SessionStatus.DEGRADED): "is being planned (some sources were unavailable)",
    str(SessionStatus.CHECKOUT_READY): "is ready for checkout",
    str(SessionStatus.ORDERED): "was placed",
}


def session_cart_total(session: Session) -> Decimal:
    return sum(
        (item.price * item.quantity for item in session.cart_items),
        Decimal("0"),
    )


def build_history_reply(session: Session, guest_short_url: str) -> str:
    """Render the last-order summary for the session's own host."""
    status_phrase = _STATUS_PHRASES.get(str(session.status), "is in progress")
    item_count = sum(item.quantity for item in session.cart_items)
    total = session_cart_total(session)
    when = session.created_at.strftime("%d %b, %H:%M")
    lines = [
        f"Your last order {status_phrase} — started {when}.",
        f"{item_count} item(s), about INR {total:.2f}.",
        f"Review it here: {guest_short_url}",
        "Live delivery tracking isn't available yet.",
    ]
    return "\n".join(lines)


async def answer_order_history(
    db: IDBAdapter,
    short_links: IShortLinkService,
    *,
    wa_id: str,
    public_app_base_url: str,
) -> str:
    """Answer an order-history/status question from durable session data."""
    session = await db.get_latest_session_for_host(wa_id)
    if session is None:
        return NO_HISTORY_REPLY
    guest_short_url = await short_links.create_short_url(
        public_app_base_url,
        f"/session/{session.session_id}?token={session.guest_token}",
    )
    return build_history_reply(session, guest_short_url)
