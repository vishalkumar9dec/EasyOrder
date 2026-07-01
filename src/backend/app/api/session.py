from __future__ import annotations

from decimal import Decimal
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from pydantic import BaseModel, Field, ValidationError

from app.models.session import (
    CartItem,
    CartItemResponse,
    DietaryTag,
    Session,
    SessionBootstrapResponse,
    SessionRole,
    SessionStatus,
    Vertical,
    hash_host_token,
)
from app.services.protocols import IDBAdapter

router = APIRouter(prefix="/api/session", tags=["session"])


class CartItemCreateRequest(BaseModel):
    item_id: str | None = None
    name: str = Field(min_length=1, max_length=120)
    quantity: int = Field(ge=1, le=99)
    price: Decimal = Field(gt=Decimal("0"))
    dietary_tag: DietaryTag = DietaryTag.ANY
    vertical: Vertical
    restaurant_id: str | None = None
    restaurant_name: str | None = None
    brand_name: str | None = None
    source_label: str | None = None


class CartItemUpdateRequest(BaseModel):
    quantity: int | None = Field(default=None, ge=0, le=99)
    price: Decimal | None = Field(default=None, gt=Decimal("0"))
    dietary_tag: DietaryTag | None = None
    restaurant_id: str | None = None
    restaurant_name: str | None = None
    brand_name: str | None = None
    source_label: str | None = None


def get_db_adapter(request: Request) -> IDBAdapter:
    return request.app.state.db_adapter


@router.get("/{session_id}")
async def get_session_bootstrap(
    session_id: str,
    token: str = Query(min_length=1),
    db: IDBAdapter = Depends(get_db_adapter),
) -> SessionBootstrapResponse:
    session = await db.get_session(session_id)
    if session is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Session not found")

    role = authorize_session_role(session, token)
    if role is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid session token",
        )

    return build_session_bootstrap_response(session, role)


@router.post("/{session_id}/cart-items", status_code=status.HTTP_201_CREATED)
async def create_cart_item(
    session_id: str,
    payload: CartItemCreateRequest,
    token: str = Query(min_length=1),
    db: IDBAdapter = Depends(get_db_adapter),
) -> SessionBootstrapResponse:
    session, role = await get_authorized_session(session_id, token, db)
    cart_item = validate_cart_item(
        {
            "item_id": payload.item_id or f"manual-{uuid4().hex[:10]}",
            "name": payload.name,
            "quantity": payload.quantity,
            "price": payload.price,
            "added_by": role.value,
            "dietary_tag": payload.dietary_tag,
            "vertical": payload.vertical,
            "restaurant_id": payload.restaurant_id,
            "restaurant_name": payload.restaurant_name,
            "brand_name": payload.brand_name,
            "source_label": payload.source_label,
        }
    )
    session.cart_items = await db.update_cart_items(
        session.session_id,
        [*session.cart_items, cart_item],
    )
    return build_session_bootstrap_response(session, role)


@router.patch("/{session_id}/cart-items/{cart_item_id}")
async def update_cart_item(
    session_id: str,
    cart_item_id: int,
    payload: CartItemUpdateRequest,
    token: str = Query(min_length=1),
    db: IDBAdapter = Depends(get_db_adapter),
) -> SessionBootstrapResponse:
    session, role = await get_authorized_session(session_id, token, db)
    index = find_cart_item_index(session, cart_item_id)
    existing = session.cart_items[index]
    updated = validate_cart_item(
        existing.model_dump() | payload.model_dump(exclude_unset=True),
    )
    next_items = [*session.cart_items]
    if updated.quantity == 0:
        next_items.pop(index)
    else:
        next_items[index] = updated
    session.cart_items = await db.update_cart_items(session.session_id, next_items)
    return build_session_bootstrap_response(session, role)


@router.delete("/{session_id}/cart-items/{cart_item_id}")
async def delete_cart_item(
    session_id: str,
    cart_item_id: int,
    token: str = Query(min_length=1),
    db: IDBAdapter = Depends(get_db_adapter),
) -> SessionBootstrapResponse:
    session, role = await get_authorized_session(session_id, token, db)
    index = find_cart_item_index(session, cart_item_id)
    next_items = [*session.cart_items]
    next_items.pop(index)
    session.cart_items = await db.update_cart_items(session.session_id, next_items)
    return build_session_bootstrap_response(session, role)


async def get_authorized_session(
    session_id: str,
    token: str,
    db: IDBAdapter,
) -> tuple[Session, SessionRole]:
    session = await db.get_session(session_id)
    if session is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Session not found")

    role = authorize_session_role(session, token)
    if role is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid session token",
        )
    return session, role


def find_cart_item_index(session: Session, cart_item_id: int) -> int:
    for index, item in enumerate(session.cart_items):
        if item.id == cart_item_id:
            return index
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Cart item not found")


def validate_cart_item(data: dict) -> CartItem:
    try:
        return CartItem(**data)
    except ValidationError as error:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=[{"loc": err["loc"], "msg": err["msg"]} for err in error.errors()],
        ) from error


def authorize_session_role(session: Session, token: str) -> SessionRole | None:
    if token == session.guest_token:
        return SessionRole.GUEST
    if hash_host_token(token) == session.host_token_hash:
        return SessionRole.HOST
    return None


def build_session_bootstrap_response(
    session: Session,
    role: SessionRole,
) -> SessionBootstrapResponse:
    return SessionBootstrapResponse(
        session_id=session.session_id,
        role=role,
        status=session.status,
        budget_limit=session.budget_limit,
        head_count=session.head_count,
        dietary_preference=session.dietary_preference,
        budget_warning=session.budget_warning,
        degraded_verticals=session.degraded_verticals,
        warnings=session.warnings,
        cart_items=[cart_item_response(item) for item in session.cart_items],
        checkout_eligible=is_checkout_eligible(session, role),
    )


def cart_item_response(item: CartItem) -> CartItemResponse:
    return CartItemResponse(
        id=item.id,
        item_id=item.item_id,
        name=item.name,
        quantity=item.quantity,
        price=item.price,
        added_by=item.added_by,
        dietary_tag=item.dietary_tag,
        vertical=item.vertical,
        restaurant_id=item.restaurant_id,
        restaurant_name=item.restaurant_name,
        brand_name=item.brand_name,
        source_label=item.source_label,
    )


def is_checkout_eligible(session: Session, role: SessionRole) -> bool:
    return role == SessionRole.HOST and session.status in {
        SessionStatus.ACTIVE,
        SessionStatus.DEGRADED,
        SessionStatus.CHECKOUT_READY,
    } and bool(session.cart_items)
