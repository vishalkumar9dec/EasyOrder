from __future__ import annotations

from decimal import Decimal
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from pydantic import BaseModel, Field, ValidationError

from app.models.session import (
    CartItem,
    CartItemResponse,
    CheckoutConfirmRequest,
    CheckoutConfirmResponse,
    CheckoutGroup,
    CheckoutIssue,
    CheckoutStepResult,
    CheckoutValidationResponse,
    DietaryTag,
    Session,
    SessionBootstrapResponse,
    SessionRole,
    SessionStatus,
    Vertical,
    hash_host_token,
)
from app.services.mock_swiggy import MockSwiggyItemUnavailableError
from app.services.protocols import IDBAdapter, ISwiggyMcpClient

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


def get_swiggy_client(request: Request) -> ISwiggyMcpClient:
    return request.app.state.swiggy_client


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


@router.post("/{session_id}/checkout")
async def validate_checkout(
    session_id: str,
    token: str = Query(min_length=1),
    db: IDBAdapter = Depends(get_db_adapter),
    swiggy: ISwiggyMcpClient = Depends(get_swiggy_client),
) -> CheckoutValidationResponse:
    session, role = await get_authorized_session(session_id, token, db)
    if role != SessionRole.HOST:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only the host can validate checkout",
        )
    if not session.cart_items:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=CheckoutValidationResponse(
                status="blocked",
                checkout_ready=False,
                groups=[],
                issues=[
                    CheckoutIssue(
                        code="EMPTY_CART",
                        message="Add at least one item before checkout.",
                        vertical=Vertical.FOOD,
                    )
                ],
            ).model_dump(mode="json"),
        )

    groups = build_checkout_groups(session.cart_items)
    issues: list[CheckoutIssue] = []
    for group in groups:
        issues.extend(await validate_checkout_group(group, swiggy))

    if issues:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=CheckoutValidationResponse(
                status="blocked",
                checkout_ready=False,
                groups=groups,
                issues=issues,
            ).model_dump(mode="json"),
        )

    await db.update_session_status(session.session_id, SessionStatus.CHECKOUT_READY)
    return CheckoutValidationResponse(
        status="checkout_ready",
        checkout_ready=True,
        groups=groups,
    )


@router.post("/{session_id}/checkout/confirm")
async def confirm_checkout(
    session_id: str,
    payload: CheckoutConfirmRequest,
    token: str = Query(min_length=1),
    db: IDBAdapter = Depends(get_db_adapter),
    swiggy: ISwiggyMcpClient = Depends(get_swiggy_client),
) -> CheckoutConfirmResponse:
    session, role = await get_authorized_session(session_id, token, db)
    if role != SessionRole.HOST:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only the host can confirm checkout",
        )
    if not session.cart_items:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Cart is empty")

    try:
        auth_header = await swiggy.exchange_oauth_code(payload.oauth_code)
    except Exception as error:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Swiggy OAuth exchange failed",
        ) from error

    steps: list[CheckoutStepResult] = []
    for group in build_checkout_groups(session.cart_items):
        steps.append(await create_checkout_step(group, auth_header, swiggy))

    created_steps = [step for step in steps if step.status == "created"]
    failed_steps = [step for step in steps if step.status != "created"]
    if failed_steps and created_steps:
        await db.update_session_status(session.session_id, SessionStatus.CHECKOUT_PARTIAL)
        return CheckoutConfirmResponse(
            status="partial",
            checkout_complete=False,
            partial_success=True,
            steps=steps,
        )
    if failed_steps:
        await db.update_session_status(session.session_id, SessionStatus.CHECKOUT_READY)
        return CheckoutConfirmResponse(
            status="blocked",
            checkout_complete=False,
            partial_success=False,
            steps=steps,
        )

    await db.update_session_status(session.session_id, SessionStatus.ORDERED)
    return CheckoutConfirmResponse(
        status="created",
        checkout_complete=True,
        partial_success=False,
        steps=steps,
    )


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


def build_checkout_groups(items: list[CartItem]) -> list[CheckoutGroup]:
    grouped: dict[str, list[CartItem]] = {}
    for item in items:
        if item.vertical == Vertical.FOOD:
            key = f"food:{item.restaurant_id}"
        else:
            key = "instamart:default"
        grouped.setdefault(key, []).append(item)

    groups: list[CheckoutGroup] = []
    for key, group_items in grouped.items():
        first = group_items[0]
        vertical = Vertical(first.vertical)
        if vertical == Vertical.FOOD:
            source_id = first.restaurant_id or "unknown-restaurant"
            source_label = first.restaurant_name or "Unknown restaurant"
        else:
            source_id = "instamart"
            source_label = first.source_label or "Instamart"
        groups.append(
            CheckoutGroup(
                group_id=f"{vertical.value}:{source_id}",
                vertical=vertical,
                source_id=source_id,
                source_label=source_label,
                item_count=sum(item.quantity for item in group_items),
                subtotal=sum((item.price * item.quantity for item in group_items), Decimal("0.00")),
                items=[cart_item_response(item) for item in group_items],
            )
        )

    return sorted(groups, key=lambda group: (group.vertical != Vertical.FOOD, group.source_label))


async def validate_checkout_group(
    group: CheckoutGroup,
    swiggy: ISwiggyMcpClient,
) -> list[CheckoutIssue]:
    try:
        result = await swiggy.create_cart(
            auth_header="Bearer mock-precheckout-validation",
            vertical=group.vertical,
            items=[checkout_payload_item(item) for item in group.items],
        )
    except MockSwiggyItemUnavailableError as error:
        item_id = str(error).split(" ", maxsplit=1)[0]
        substitutes = await swiggy.get_substitute_items(item_id)
        return [
            CheckoutIssue(
                code="ITEM_UNAVAILABLE",
                message=f"{item_id} is unavailable before checkout.",
                vertical=group.vertical,
                item_id=item_id,
                source_label=group.source_label,
                substitutes=[
                    cart_item_response(validate_cart_item(substitute_item_payload(substitute_item)))
                    for substitute_item in substitutes
                ],
            )
        ]

    if result.get("status") == "price_changed":
        return [
            CheckoutIssue(
                code="PRICE_CHANGED",
                message=f"{result['item_id']} changed price before checkout.",
                vertical=group.vertical,
                item_id=result["item_id"],
                source_label=group.source_label,
                new_price=Decimal(str(result["new_price"])),
            )
        ]
    return []


async def create_checkout_step(
    group: CheckoutGroup,
    auth_header: str,
    swiggy: ISwiggyMcpClient,
) -> CheckoutStepResult:
    try:
        result = await swiggy.create_cart(
            auth_header=auth_header,
            vertical=group.vertical,
            items=[checkout_payload_item(item) for item in group.items],
        )
    except Exception as error:
        return CheckoutStepResult(
            group_id=group.group_id,
            vertical=group.vertical,
            source_label=group.source_label,
            status="failed",
            error_message=f"{error.__class__.__name__}: checkout cart creation failed",
        )

    if result.get("status") != "created":
        return CheckoutStepResult(
            group_id=group.group_id,
            vertical=group.vertical,
            source_label=group.source_label,
            status=str(result.get("status", "failed")),
            error_message="Checkout cart creation did not complete.",
        )

    return CheckoutStepResult(
        group_id=group.group_id,
        vertical=group.vertical,
        source_label=group.source_label,
        status="created",
        checkout_url=str(result["checkout_url"]),
    )


def substitute_item_payload(item: dict[str, object]) -> dict[str, object]:
    return {"added_by": "swiggy", "quantity": 1, **item}


def checkout_payload_item(item: CartItemResponse) -> dict[str, object]:
    return {
        "item_id": item.item_id,
        "name": item.name,
        "quantity": item.quantity,
        "price": str(item.price),
        "vertical": item.vertical,
        "restaurant_id": item.restaurant_id,
        "restaurant_name": item.restaurant_name,
        "brand_name": item.brand_name,
        "source_label": item.source_label,
    }


def is_checkout_eligible(session: Session, role: SessionRole) -> bool:
    return role == SessionRole.HOST and session.status in {
        SessionStatus.ACTIVE,
        SessionStatus.DEGRADED,
        SessionStatus.CHECKOUT_READY,
    } and bool(session.cart_items)
