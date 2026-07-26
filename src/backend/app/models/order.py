"""Targeted single-restaurant order domain models.

A deliberately separate concept from Session: a Session is a shared,
multi-item, multi-guest group-planning cart; an Order here is a single
restaurant, single requester, host-only order placed (or scheduled) in one
shot from a targeted WhatsApp prompt ("order X from Y").
"""

from __future__ import annotations

import uuid
from datetime import UTC, datetime
from decimal import Decimal
from enum import StrEnum
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator


class OrderStatus(StrEnum):
    """Lifecycle states of a targeted order."""

    PENDING_CONFIRMATION = "PENDING_CONFIRMATION"
    SCHEDULED = "SCHEDULED"
    PLACED = "PLACED"
    DELIVERED = "DELIVERED"
    CANCELLED = "CANCELLED"
    FAILED = "FAILED"


class OrderLineItem(BaseModel):
    """A single dish within a targeted order."""

    item_id: str
    name: str
    price: Decimal = Field(gt=Decimal("0"))
    quantity: int = Field(default=1, ge=1, le=99)

    @field_validator("price", mode="before")
    @classmethod
    def normalize_price(cls, value: Decimal | float | int | str) -> Decimal:
        return Decimal(str(value)).quantize(Decimal("0.01"))


class OrderCreate(BaseModel):
    """Inputs needed to create a persisted order."""

    wa_id: str
    restaurant_id: str
    restaurant_name: str
    items: list[OrderLineItem]
    total: Decimal = Field(gt=Decimal("0"))
    budget_limit: Decimal | None = None
    delivery_deadline: datetime | None = None
    target_placement_at: datetime | None = None
    status: OrderStatus = OrderStatus.PLACED
    source_message_id: str | None = None

    model_config = ConfigDict(use_enum_values=True)

    @field_validator("total", mode="before")
    @classmethod
    def normalize_total(cls, value: Decimal | float | int | str) -> Decimal:
        return Decimal(str(value)).quantize(Decimal("0.01"))

    @field_validator("budget_limit", mode="before")
    @classmethod
    def normalize_budget_limit(cls, value: Decimal | float | int | str | None) -> Decimal | None:
        if value is None:
            return None
        return Decimal(str(value)).quantize(Decimal("0.01"))


class Order(OrderCreate):
    """Persisted targeted order."""

    order_id: str = Field(default_factory=lambda: f"order_{uuid.uuid4().hex[:12]}")
    swiggy_order_id: str | None = None
    failure_reason: str | None = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))

    model_config = ConfigDict(use_enum_values=True)


def order_bucket(status: OrderStatus | str) -> Literal["scheduled", "ongoing", "historical"]:
    """Bucket an order status for the Scheduled/Ongoing/Historical UI page."""
    status_value = OrderStatus(status)
    if status_value in (OrderStatus.PENDING_CONFIRMATION, OrderStatus.SCHEDULED):
        return "scheduled"
    if status_value == OrderStatus.PLACED:
        return "ongoing"
    return "historical"  # DELIVERED, CANCELLED, FAILED
