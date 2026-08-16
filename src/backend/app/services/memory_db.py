"""In-memory persistence adapters for local agent and API tests."""

from __future__ import annotations

from collections.abc import Sequence
from datetime import UTC, datetime
from decimal import Decimal

from app.models.order import Order, OrderCreate, OrderLineItem, OrderStatus
from app.models.session import CartItem, Session, SessionCreate, SessionEvent, SessionStatus
from app.models.spend import (
    SPENT_ORDER_STATUSES,
    SPENT_SESSION_STATUSES,
    SpendBucket,
    SpendSummary,
)
from app.services.protocols import IDBAdapter, ISessionStore


class InMemoryDBAdapter(IDBAdapter, ISessionStore):
    """Small IDBAdapter implementation used in local mock mode."""

    def __init__(self) -> None:
        self.sessions: dict[str, Session] = {}
        self.events: list[SessionEvent] = []
        self.next_cart_id = 1
        self._next_event_id = 1
        self.orders: dict[str, Order] = {}

    async def create_session(
        self,
        session: SessionCreate | Session,
        host_token_hash: str | None = None,
        guest_token: str | None = None,
        cart_items: Sequence[CartItem] | None = None,
    ) -> Session:
        if isinstance(session, Session):
            created = session
        else:
            if host_token_hash is None or guest_token is None:
                raise ValueError("host_token_hash and guest_token are required")
            created = Session(
                whatsapp_group_id=session.whatsapp_group_id,
                host_phone=session.host_phone,
                host_token_hash=host_token_hash,
                guest_token=guest_token,
                budget_limit=session.budget_limit,
                head_count=session.head_count,
                dietary_preference=session.dietary_preference,
                status=session.status,
                budget_warning=session.budget_warning,
                degraded_verticals=session.degraded_verticals,
                warnings=session.warnings,
            )

        created.cart_items = self._assign_cart(created.session_id, cart_items or created.cart_items)
        self.sessions[created.session_id] = created
        return created

    async def get_session(self, session_id: str) -> Session | None:
        return self.sessions.get(session_id)

    async def get_latest_session_for_host(self, host_phone: str) -> Session | None:
        candidates = [s for s in self.sessions.values() if s.host_phone == host_phone]
        if not candidates:
            return None
        return max(candidates, key=lambda s: (s.created_at, s.session_id))

    async def list_sessions_for_host(self, host_phone: str, *, limit: int = 10) -> list[Session]:
        candidates = [s for s in self.sessions.values() if s.host_phone == host_phone]
        candidates.sort(key=lambda s: (s.created_at, s.session_id), reverse=True)
        return candidates[:limit]

    async def delete_sessions_for_host(self, host_phone: str) -> int:
        to_delete = [
            session_id
            for session_id, session in self.sessions.items()
            if session.host_phone == host_phone
        ]
        for session_id in to_delete:
            del self.sessions[session_id]
        self.events = [e for e in self.events if e.session_id not in to_delete]
        return len(to_delete)

    async def delete_sessions_older_than(self, cutoff: datetime) -> int:
        to_delete = [
            session_id
            for session_id, session in self.sessions.items()
            if session.created_at < cutoff
        ]
        for session_id in to_delete:
            del self.sessions[session_id]
        self.events = [e for e in self.events if e.session_id not in to_delete]
        return len(to_delete)

    async def update_cart_items(self, session_id: str, items: Sequence[CartItem]) -> list[CartItem]:
        session = self.sessions[session_id]
        session.cart_items = self._assign_cart(session_id, items)
        return session.cart_items

    async def update_session_status(self, session_id: str, status: SessionStatus | str) -> None:
        if session := self.sessions.get(session_id):
            session.status = status  # type: ignore[assignment]

    async def insert_session_event(self, event: SessionEvent) -> SessionEvent | None:
        from datetime import UTC, datetime

        # Mirror the unique (message_id, event_type) index: reject duplicates
        # so webhook retries cannot double-record ledger events.
        if event.message_id is not None and await self.get_session_event(
            event.message_id, str(event.event_type)
        ):
            return None
        stored = event.model_copy(
            update={"id": self._next_event_id, "created_at": datetime.now(UTC)}
        )
        self._next_event_id += 1
        self.events.append(stored)
        return stored

    async def get_session_event(self, message_id: str, event_type: str) -> SessionEvent | None:
        for event in self.events:
            if event.message_id == message_id and str(event.event_type) == str(event_type):
                return event
        return None

    async def get_session_events(self, session_id: str) -> list[SessionEvent]:
        return [e for e in self.events if e.session_id == session_id]

    async def create_order(self, order: OrderCreate) -> Order:
        created = Order(**order.model_dump())
        self.orders[created.order_id] = created
        return created

    async def get_order(self, order_id: str) -> Order | None:
        return self.orders.get(order_id)

    async def get_order_by_source_message_id(self, message_id: str) -> Order | None:
        for order in self.orders.values():
            if order.source_message_id == message_id:
                return order
        return None

    async def get_pending_confirmation_order(self, wa_id: str) -> Order | None:
        for order in self.orders.values():
            if order.wa_id == wa_id and order.status == OrderStatus.PENDING_CONFIRMATION:
                return order
        return None

    async def list_orders_for_host(self, wa_id: str, *, limit: int = 30) -> list[Order]:
        candidates = [order for order in self.orders.values() if order.wa_id == wa_id]
        candidates.sort(key=lambda o: (o.created_at, o.order_id), reverse=True)
        return candidates[:limit]

    async def get_spend_summary(self, wa_id: str) -> SpendSummary:
        spent_sessions = [
            session
            for session in self.sessions.values()
            if session.host_phone == wa_id and session.status in SPENT_SESSION_STATUSES
        ]
        spent_orders = [
            order
            for order in self.orders.values()
            if order.wa_id == wa_id and order.status in SPENT_ORDER_STATUSES
        ]
        session_total = sum(
            (
                item.price * item.quantity
                for session in spent_sessions
                for item in session.cart_items
            ),
            Decimal("0"),
        )
        order_total = sum((order.total for order in spent_orders), Decimal("0"))
        return SpendSummary(
            group_orders=SpendBucket(total=session_total, count=len(spent_sessions)),
            restaurant_orders=SpendBucket(total=order_total, count=len(spent_orders)),
        )

    async def get_due_scheduled_orders(
        self,
        *,
        as_of: datetime,
        limit: int = 20,
    ) -> list[Order]:
        due = [
            order
            for order in self.orders.values()
            if order.status == OrderStatus.SCHEDULED
            and order.target_placement_at is not None
            and order.target_placement_at <= as_of
        ]
        due.sort(key=lambda o: o.target_placement_at)  # type: ignore[arg-type,return-value]
        return due[:limit]

    async def update_order_status(self, order_id: str, status: OrderStatus | str) -> None:
        if order := self.orders.get(order_id):
            order.status = status  # type: ignore[assignment]
            order.updated_at = datetime.now(UTC)

    async def set_order_scheduled(self, order_id: str, *, target_placement_at: datetime) -> None:
        if order := self.orders.get(order_id):
            order.status = OrderStatus.SCHEDULED  # type: ignore[assignment]
            order.target_placement_at = target_placement_at
            order.updated_at = datetime.now(UTC)

    async def set_order_placed(self, order_id: str, *, swiggy_order_id: str) -> None:
        if order := self.orders.get(order_id):
            order.status = OrderStatus.PLACED  # type: ignore[assignment]
            order.swiggy_order_id = swiggy_order_id
            order.updated_at = datetime.now(UTC)

    async def set_order_failed(self, order_id: str, *, failure_reason: str) -> None:
        if order := self.orders.get(order_id):
            order.status = OrderStatus.FAILED  # type: ignore[assignment]
            order.failure_reason = failure_reason
            order.updated_at = datetime.now(UTC)

    async def set_order_price_changed(
        self,
        order_id: str,
        *,
        items: Sequence[OrderLineItem],
        total: Decimal,
    ) -> None:
        if order := self.orders.get(order_id):
            order.status = OrderStatus.PENDING_CONFIRMATION  # type: ignore[assignment]
            order.items = list(items)
            order.total = Decimal(str(total)).quantize(Decimal("0.01"))
            order.updated_at = datetime.now(UTC)

    def _assign_cart(self, session_id: str, items: Sequence[CartItem]) -> list[CartItem]:
        assigned: list[CartItem] = []
        for item in items:
            assigned_item = item.model_copy(
                update={
                    "id": item.id or self.next_cart_id,
                    "session_id": session_id,
                }
            )
            if item.id is None:
                self.next_cart_id += 1
            assigned.append(assigned_item)
        return assigned
