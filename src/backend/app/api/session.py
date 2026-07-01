from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status

from app.models.session import (
    CartItem,
    CartItemResponse,
    Session,
    SessionBootstrapResponse,
    SessionRole,
    SessionStatus,
    hash_host_token,
)
from app.services.protocols import IDBAdapter

router = APIRouter(prefix="/api/session", tags=["session"])


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
