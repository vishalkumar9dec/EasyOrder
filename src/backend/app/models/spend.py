"""Spend rollup across both order surfaces a host can create.

EasyOrder produces two different kinds of purchase, and a host's spend is the
sum of both:

* **Group orders** — a shared planning Session that reached `ORDERED`. Its
  value is the cart total (price x quantity over every cart item).
* **Restaurant orders** — a targeted single-restaurant `Order` that was
  actually placed (`PLACED` or `DELIVERED`).

Only money that was actually committed counts. A session still being planned,
an order still waiting for confirmation or scheduled for later, and a cancelled
or failed order all contribute nothing — they are intent, not spend.

This is computed from EasyOrder's own records by design: these are the orders
placed through EasyOrder, so the answer is already local. Asking Swiggy over
MCP for it would be a slower, costlier route to a number we already hold.
"""

from __future__ import annotations

from decimal import Decimal

from pydantic import BaseModel, Field

from app.models.order import OrderStatus
from app.models.session import SessionStatus

#: Session statuses that represent money actually committed.
SPENT_SESSION_STATUSES: frozenset[SessionStatus] = frozenset({SessionStatus.ORDERED})

#: Order statuses that represent money actually committed.
SPENT_ORDER_STATUSES: frozenset[OrderStatus] = frozenset(
    {OrderStatus.PLACED, OrderStatus.DELIVERED}
)


class SpendBucket(BaseModel):
    """One surface's contribution to total spend."""

    total: Decimal = Field(default=Decimal("0"), ge=Decimal("0"))
    count: int = Field(default=0, ge=0)


class SpendSummary(BaseModel):
    """A host's lifetime spend through EasyOrder, split by surface.

    Not windowed by the page-size limits of the orders listings — the whole
    point of a total is that it counts everything, including orders too old to
    still be on screen.
    """

    group_orders: SpendBucket = Field(default_factory=SpendBucket)
    restaurant_orders: SpendBucket = Field(default_factory=SpendBucket)

    @property
    def total(self) -> Decimal:
        return self.group_orders.total + self.restaurant_orders.total

    @property
    def order_count(self) -> int:
        return self.group_orders.count + self.restaurant_orders.count
