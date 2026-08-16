"""Learned ordering preferences for one WhatsApp user.

Derived from what the user has actually ordered through EasyOrder: targeted
restaurant orders that were placed or delivered, and group sessions that
reached ORDERED. Nothing here is inferred by a language model — every field is
an arithmetic summary of committed orders, so the same history always produces
the same profile and every value can be traced back to the rows it came from.

The profile is rebuilt from source on each use rather than cached, which is why
there is no staleness or invalidation machinery: an order placed a second ago
is already part of it.
"""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, Field

from app.models.session import DietaryTag

#: Orders needed before a profile is allowed to fill anything in. A default
#: guessed from one or two orders is worse than no default: it is usually wrong,
#: and it teaches the user the system does not know them.
MIN_OBSERVATIONS = 3

#: A dietary tendency has to be this dominant before it becomes a default.
#: Ordering veg twice out of five times is not a preference.
DIETARY_MAJORITY = 0.6

#: How many favourite restaurants to keep.
FAVOURITES_KEPT = 3


class RestaurantAffinity(BaseModel):
    """One restaurant the user returns to, and how strongly."""

    restaurant_name: str
    order_count: int = Field(ge=1)
    last_ordered_at: datetime


class UserProfile(BaseModel):
    """What EasyOrder has learned about how one user orders.

    Every field is optional: a user with no history gets an empty profile, and
    an empty profile fills nothing. `observations` is the gate — below
    `MIN_OBSERVATIONS` the profile is still built and still readable, but
    `is_confident` is False and the graph will not apply it.
    """

    wa_id: str
    observations: int = Field(default=0, ge=0)
    typical_budget: Decimal | None = None
    budget_ceiling: Decimal | None = None
    usual_headcount: int | None = None
    dietary_tendency: DietaryTag | None = None
    favourites: list[RestaurantAffinity] = Field(default_factory=list)
    busiest_weekday: str | None = None
    busiest_hour: int | None = None
    last_ordered_at: datetime | None = None

    @property
    def is_confident(self) -> bool:
        return self.observations >= MIN_OBSERVATIONS

    @property
    def favourite_restaurant(self) -> str | None:
        return self.favourites[0].restaurant_name if self.favourites else None
