"""WhatsApp OTP login and account API (task 11.1, ADR 0006).

One account API for all surfaces: the PWA calls these endpoints with a web
session cookie; the WhatsApp webhook derives the same answers from the same
service layer using the verified inbound wa_id.
"""

from __future__ import annotations

import logging

from fastapi import APIRouter, Cookie, HTTPException, Request, Response, status
from pydantic import BaseModel, Field

from app.config import Settings, get_settings
from app.models.order import Order, order_bucket
from app.models.profile import MIN_OBSERVATIONS
from app.models.session import Session
from app.services.order_history import session_cart_total
from app.services.profile_builder import load_profile
from app.services.protocols import IDBAdapter, IShortLinkService, IWhatsAppSender
from app.services.web_auth import (
    WEB_SESSION_COOKIE,
    WEB_SESSION_TTL,
    InvalidPhoneError,
    normalize_phone,
    otp_message,
    resolve_web_session,
    revoke_web_session,
    start_login,
    verify_login,
)
from app.services.whatsapp_sender import WhatsAppSendError

router = APIRouter(prefix="/api", tags=["account"])
logger = logging.getLogger("easyorder.api")


class OtpRequest(BaseModel):
    phone: str = Field(min_length=8, max_length=20)


class OtpVerify(BaseModel):
    phone: str = Field(min_length=8, max_length=20)
    code: str = Field(min_length=4, max_length=8)


def get_auth_store(request: Request):
    return request.app.state.auth_store


def get_db(request: Request) -> IDBAdapter:
    return request.app.state.db_adapter


def get_sender(request: Request) -> IWhatsAppSender:
    return request.app.state.whatsapp_sender


def get_short_links(request: Request) -> IShortLinkService:
    return request.app.state.short_links


def _client_ip(request: Request) -> str | None:
    forwarded = request.headers.get("x-forwarded-for")
    if forwarded:
        return forwarded.split(",")[0].strip() or None
    return request.client.host if request.client else None


async def require_wa_id(request: Request, token: str | None) -> str:
    wa_id = await resolve_web_session(get_auth_store(request), token)
    if wa_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Login required",
        )
    return wa_id


@router.post("/auth/otp/request")
async def request_otp(payload: OtpRequest, request: Request) -> dict[str, str]:
    try:
        wa_id = normalize_phone(payload.phone)
    except InvalidPhoneError as error:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(error)
        ) from error

    limiter = getattr(request.app.state, "otp_rate_limiter", None)
    if limiter is not None and not limiter.allow(wa_id, _client_ip(request)):
        logger.warning("otp_rate_limited wa_id_suffix=%s", wa_id[-4:])
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Too many login code requests. Try again in a few minutes.",
        )

    code = await start_login(get_auth_store(request), wa_id)
    try:
        await get_sender(request).send_private_message(wa_id, otp_message(code))
    except WhatsAppSendError:
        logger.warning("otp_send_failed wa_id_suffix=%s", wa_id[-4:])
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Could not send the login code over WhatsApp",
        ) from None
    logger.info("otp_sent wa_id_suffix=%s", wa_id[-4:])
    return {"status": "sent"}


@router.post("/auth/otp/verify")
async def verify_otp(payload: OtpVerify, request: Request, response: Response) -> dict[str, str]:
    try:
        wa_id = normalize_phone(payload.phone)
    except InvalidPhoneError as error:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(error)
        ) from error

    token = await verify_login(get_auth_store(request), wa_id, payload.code)
    if token is None:
        logger.info("otp_verify_failed wa_id_suffix=%s", wa_id[-4:])
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired code",
        )

    settings: Settings = get_settings()
    response.set_cookie(
        WEB_SESSION_COOKIE,
        token,
        max_age=int(WEB_SESSION_TTL.total_seconds()),
        httponly=True,
        samesite="lax",
        secure=settings.app_env != "local",
        path="/",
    )
    logger.info("web_login wa_id_suffix=%s", wa_id[-4:])
    return {"status": "ok", "wa_id": wa_id}


@router.post("/auth/logout")
async def logout(
    request: Request,
    response: Response,
    easyorder_web_session: str | None = Cookie(default=None),
) -> dict[str, str]:
    await revoke_web_session(get_auth_store(request), easyorder_web_session)
    response.delete_cookie(WEB_SESSION_COOKIE, path="/")
    return {"status": "logged_out"}


@router.get("/me")
async def me(
    request: Request,
    easyorder_web_session: str | None = Cookie(default=None),
) -> dict[str, str]:
    wa_id = await require_wa_id(request, easyorder_web_session)
    return {"wa_id": wa_id}


@router.get("/me/orders")
async def my_orders(
    request: Request,
    easyorder_web_session: str | None = Cookie(default=None),
) -> dict[str, object]:
    wa_id = await require_wa_id(request, easyorder_web_session)
    settings: Settings = get_settings()
    sessions = await get_db(request).list_sessions_for_host(wa_id, limit=20)
    short_links = get_short_links(request)
    orders = []
    for session in sessions:
        orders.append(await _order_entry(session, short_links, settings))
    return {"wa_id": wa_id, "orders": orders}


@router.get("/me/orders/live")
async def my_live_orders(
    request: Request,
    easyorder_web_session: str | None = Cookie(default=None),
) -> dict[str, object]:
    wa_id = await require_wa_id(request, easyorder_web_session)
    orders = await get_db(request).list_orders_for_host(wa_id, limit=30)
    buckets: dict[str, list[dict[str, object]]] = {
        "scheduled": [],
        "ongoing": [],
        "historical": [],
    }
    for order in orders:
        buckets[order_bucket(order.status)].append(_live_order_entry(order))
    return {"wa_id": wa_id, **buckets}


@router.get("/me/profile")
async def my_profile(
    request: Request,
    easyorder_web_session: str | None = Cookie(default=None),
) -> dict[str, object]:
    """What EasyOrder has learned about how this user orders.

    The same profile the agent graph applies when a prompt leaves something
    unsaid, exposed so the user can see it — a preference you cannot inspect is
    one you cannot disagree with. Derived live, so this is never a stale copy of
    what the graph used.
    """
    wa_id = await require_wa_id(request, easyorder_web_session)
    profile = await load_profile(get_db(request), wa_id)
    return {
        "wa_id": wa_id,
        "observations": profile.observations,
        "is_confident": profile.is_confident,
        "min_observations": MIN_OBSERVATIONS,
        "typical_budget": (
            f"{profile.typical_budget:.2f}" if profile.typical_budget is not None else None
        ),
        "budget_ceiling": (
            f"{profile.budget_ceiling:.2f}" if profile.budget_ceiling is not None else None
        ),
        "usual_headcount": profile.usual_headcount,
        "dietary_tendency": (
            str(profile.dietary_tendency) if profile.dietary_tendency is not None else None
        ),
        "favourites": [
            {
                "restaurant_name": favourite.restaurant_name,
                "order_count": favourite.order_count,
                "last_ordered_at": favourite.last_ordered_at.isoformat(),
            }
            for favourite in profile.favourites
        ],
        "busiest_weekday": profile.busiest_weekday,
        "busiest_hour": profile.busiest_hour,
        "last_ordered_at": (
            profile.last_ordered_at.isoformat() if profile.last_ordered_at is not None else None
        ),
    }


@router.get("/me/spend")
async def my_spend(
    request: Request,
    easyorder_web_session: str | None = Cookie(default=None),
) -> dict[str, object]:
    """Lifetime spend for the logged-in host, split by surface.

    Answered from EasyOrder's own records: these are orders placed through
    EasyOrder, so the total is already local — no Swiggy round-trip needed.
    Counts committed money only (see `app.models.spend`), and counts all of
    it, not just the page of orders the listings show.
    """
    wa_id = await require_wa_id(request, easyorder_web_session)
    summary = await get_db(request).get_spend_summary(wa_id)
    return {
        "wa_id": wa_id,
        "currency": "INR",
        "total": f"{summary.total:.2f}",
        "order_count": summary.order_count,
        "group_orders": {
            "total": f"{summary.group_orders.total:.2f}",
            "count": summary.group_orders.count,
        },
        "restaurant_orders": {
            "total": f"{summary.restaurant_orders.total:.2f}",
            "count": summary.restaurant_orders.count,
        },
    }


def _live_order_entry(order: Order) -> dict[str, object]:
    return {
        "order_id": order.order_id,
        "restaurant_name": order.restaurant_name,
        "items": [{"name": item.name, "quantity": item.quantity} for item in order.items],
        "total": f"{order.total:.2f}",
        "status": str(order.status),
        "delivery_deadline": order.delivery_deadline.isoformat() if order.delivery_deadline else None,
        "target_placement_at": (
            order.target_placement_at.isoformat() if order.target_placement_at else None
        ),
        "created_at": order.created_at.isoformat(),
    }


async def _order_entry(
    session: Session,
    short_links: IShortLinkService,
    settings: Settings,
) -> dict[str, object]:
    review_url = await short_links.create_short_url(
        settings.public_app_base_url,
        f"/session/{session.session_id}?token={session.guest_token}",
    )
    return {
        "session_id": session.session_id,
        "created_at": session.created_at.isoformat(),
        "status": str(session.status),
        "item_count": sum(item.quantity for item in session.cart_items),
        "total": f"{session_cart_total(session):.2f}",
        "review_url": review_url,
    }
