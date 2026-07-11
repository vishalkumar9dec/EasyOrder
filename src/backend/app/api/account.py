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
from app.models.session import Session
from app.services.order_history import session_cart_total
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
