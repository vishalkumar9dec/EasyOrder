"""Session, cart, checkout, and token domain models."""

from __future__ import annotations

import hashlib
import secrets
import uuid
from datetime import UTC, datetime
from decimal import Decimal
from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

DEFAULT_BUDGET_LIMIT = Decimal("3000.00")
DEFAULT_HEAD_COUNT = 4


class SessionStatus(StrEnum):
    """Lifecycle states of an EasyOrder session."""

    INITIALIZING = "INITIALIZING"
    ACTIVE = "ACTIVE"
    DEGRADED = "DEGRADED"
    CHECKOUT_READY = "CHECKOUT_READY"
    ORDERED = "ORDERED"


class DietaryTag(StrEnum):
    """Dietary classifications used by Swiggy results and EasyOrder sessions."""

    VEG = "VEG"
    NON_VEG = "NON-VEG"
    ANY = "ANY"


class Vertical(StrEnum):
    """Swiggy verticals supported by the MVP."""

    FOOD = "food"
    INSTAMART = "instamart"


class SessionWarning(BaseModel):
    """A non-blocking warning shown to collaborators."""

    code: str
    message: str
    vertical: Vertical | None = None
    item_id: str | None = None

    model_config = ConfigDict(use_enum_values=True)


class CartItem(BaseModel):
    """A single consolidated cart item."""

    id: int | None = None
    session_id: str | None = None
    item_id: str
    name: str
    quantity: int = Field(default=1, ge=0, le=99)
    price: Decimal = Field(gt=Decimal("0"))
    added_by: str
    dietary_tag: DietaryTag = DietaryTag.ANY
    vertical: Vertical
    restaurant_id: str | None = None
    restaurant_name: str | None = None
    brand_name: str | None = None
    source_label: str | None = None
    created_at: datetime | None = None

    model_config = ConfigDict(use_enum_values=True)

    @field_validator("price", mode="before")
    @classmethod
    def normalize_price(cls, value: Decimal | float | int | str) -> Decimal:
        return Decimal(str(value)).quantize(Decimal("0.01"))

    @model_validator(mode="after")
    def require_source_attribution(self) -> CartItem:
        if self.vertical == Vertical.FOOD:
            if not self.restaurant_id or not self.restaurant_name:
                raise ValueError("Food cart items require restaurant_id and restaurant_name")
        if self.vertical == Vertical.INSTAMART and not self.source_label:
            raise ValueError("Instamart cart items require source_label")
        return self


class SessionCreate(BaseModel):
    """Inputs needed to create a persisted session."""

    whatsapp_group_id: str
    host_phone: str
    budget_limit: Decimal = DEFAULT_BUDGET_LIMIT
    head_count: int = Field(default=DEFAULT_HEAD_COUNT, ge=1, le=100)
    dietary_preference: DietaryTag = DietaryTag.ANY
    status: SessionStatus = SessionStatus.INITIALIZING
    budget_warning: bool = False
    degraded_verticals: list[Vertical] = Field(default_factory=list)
    warnings: list[SessionWarning] = Field(default_factory=list)

    model_config = ConfigDict(use_enum_values=True)

    @field_validator("budget_limit", mode="before")
    @classmethod
    def normalize_budget(cls, value: Decimal | float | int | str) -> Decimal:
        return Decimal(str(value)).quantize(Decimal("0.01"))


class Session(BaseModel):
    """Persisted EasyOrder session state."""

    session_id: str = Field(default_factory=lambda: f"session_{uuid.uuid4().hex[:12]}")
    whatsapp_group_id: str
    host_phone: str
    host_token_hash: str
    guest_token: str
    budget_limit: Decimal = DEFAULT_BUDGET_LIMIT
    head_count: int = Field(default=DEFAULT_HEAD_COUNT, ge=1, le=100)
    dietary_preference: DietaryTag = DietaryTag.ANY
    status: SessionStatus = SessionStatus.INITIALIZING
    budget_warning: bool = False
    degraded_verticals: list[Vertical] = Field(default_factory=list)
    warnings: list[SessionWarning] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    cart_items: list[CartItem] = Field(default_factory=list)

    model_config = ConfigDict(use_enum_values=True)

    @field_validator("budget_limit", mode="before")
    @classmethod
    def normalize_budget(cls, value: Decimal | float | int | str) -> Decimal:
        return Decimal(str(value)).quantize(Decimal("0.01"))


class SessionInitResponse(BaseModel):
    """Response returned after a tagged prompt initializes a session."""

    session_id: str
    host_token: str
    guest_link: str


class SessionInitResult(BaseModel):
    """Initialized session plus one-time token material for private handoff."""

    session: Session
    host_token: str


class SessionRole(StrEnum):
    """Role derived from the bootstrap token."""

    HOST = "host"
    GUEST = "guest"


class CartItemResponse(BaseModel):
    """Redacted cart item payload returned to PWA clients."""

    id: int | None = None
    item_id: str
    name: str
    quantity: int
    price: Decimal
    added_by: str
    dietary_tag: DietaryTag
    vertical: Vertical
    restaurant_id: str | None = None
    restaurant_name: str | None = None
    brand_name: str | None = None
    source_label: str | None = None

    model_config = ConfigDict(use_enum_values=True)


class SessionBootstrapResponse(BaseModel):
    """Token-authorized session state for the production PWA bootstrap."""

    session_id: str
    role: SessionRole
    status: SessionStatus
    budget_limit: Decimal
    head_count: int
    dietary_preference: DietaryTag
    budget_warning: bool
    degraded_verticals: list[Vertical]
    warnings: list[SessionWarning]
    cart_items: list[CartItemResponse]
    checkout_eligible: bool

    model_config = ConfigDict(use_enum_values=True)


class CheckoutGroup(BaseModel):
    """One Swiggy checkout payload preview."""

    group_id: str
    vertical: Vertical
    source_id: str
    source_label: str
    item_count: int
    subtotal: Decimal
    items: list[CartItemResponse]

    model_config = ConfigDict(use_enum_values=True)


class CheckoutIssue(BaseModel):
    """A blocking issue found during pre-checkout validation."""

    code: str
    message: str
    vertical: Vertical
    item_id: str | None = None
    source_label: str | None = None
    new_price: Decimal | None = None
    substitutes: list[CartItemResponse] = Field(default_factory=list)

    model_config = ConfigDict(use_enum_values=True)


class CheckoutValidationResponse(BaseModel):
    """Pre-checkout validation result returned before OAuth confirmation."""

    status: str
    checkout_ready: bool
    groups: list[CheckoutGroup]
    issues: list[CheckoutIssue] = Field(default_factory=list)

    model_config = ConfigDict(use_enum_values=True)


class GeneratedSessionTokens(BaseModel):
    """Generated raw and stored token forms for a new session."""

    host_token: str
    host_token_hash: str
    guest_token: str


def generate_host_token() -> str:
    """Generate a raw host token sent only through private host channels."""

    return f"host_{secrets.token_urlsafe(32)}"


def generate_guest_token() -> str:
    """Generate a public guest token safe to include in a group link."""

    return f"guest_{secrets.token_urlsafe(24)}"


def hash_host_token(raw_token: str) -> str:
    """SHA-256 hash a raw host token for storage and lookup."""

    return hashlib.sha256(raw_token.encode("utf-8")).hexdigest()


def generate_session_tokens() -> GeneratedSessionTokens:
    """Generate host and guest token material for a new session."""

    host_token = generate_host_token()
    return GeneratedSessionTokens(
        host_token=host_token,
        host_token_hash=hash_host_token(host_token),
        guest_token=generate_guest_token(),
    )
