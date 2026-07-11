from __future__ import annotations

import hashlib
import hmac
import logging
import re
from datetime import UTC, datetime

from fastapi import APIRouter, Depends, Header, HTTPException, Query, Request, status
from fastapi.responses import PlainTextResponse
from pydantic import ValidationError

from app.config import Settings, get_settings
from app.models.session import EventType, SessionEvent
from app.models.whatsapp import WhatsAppWebhookPayload, extract_incoming_messages
from app.services.agent import AgentRejectedPromptError, EasyOrderAgentService
from app.services.intent_router import ChatMode, classify_chat_mode, route_business_chat_message
from app.services.memory_db import InMemoryDBAdapter
from app.services.mock_agent import MockAgentService
from app.services.protocols import IAgentService, IDBAdapter, IShortLinkService, IWhatsAppSender
from app.services.swiggy_mcp import create_swiggy_client
from app.services.whatsapp_sender import SessionHandoff, WhatsAppSendError

router = APIRouter(prefix="/api/whatsapp", tags=["whatsapp"])
logger = logging.getLogger("easyorder.api")
terminal_logger = logging.getLogger("uvicorn.error")

TIMELINE_REDACTION_PATTERNS = [
    re.compile(r"\b[\w.+-]+@[\w-]+\.[\w.-]+\b"),
    re.compile(r"\b(?:\+?91[-\s]?)?[6-9]\d{9}\b"),
    re.compile(r"\b(?:\d[ -]*?){13,16}\b"),
    re.compile(r"\bhost_[A-Za-z0-9_-]+\b"),
    re.compile(r"\bguest_[A-Za-z0-9_-]+\b"),
]


def log_webhook_event(event: str, **fields: object) -> None:
    timestamp = datetime.now(UTC).isoformat()
    event_fields = {"timestamp": timestamp, **fields}
    field_text = " ".join(f"{key}={value}" for key, value in event_fields.items())
    message = f"{event} {field_text}"
    logger.info(message, extra={"event": event, **event_fields})
    terminal_logger.info(message)


def get_agent_service(request: Request) -> IAgentService:
    return request.app.state.agent_service


def get_whatsapp_sender(request: Request) -> IWhatsAppSender:
    return request.app.state.whatsapp_sender


def get_db_adapter(request: Request) -> IDBAdapter:
    return request.app.state.db_adapter


def get_short_links(request: Request) -> IShortLinkService:
    return request.app.state.short_links


def build_session_path(session_id: str, token: str) -> str:
    return f"/session/{session_id}?token={token}"


def build_session_link(base_url: str, session_id: str, token: str) -> str:
    return f"{base_url.rstrip('/')}{build_session_path(session_id, token)}"


def build_group_session_message(guest_short_url: str) -> str:
    return f"EasyOrder is ready. Open the planning canvas: {guest_short_url}"


def build_private_host_message(host_short_url: str) -> str:
    return f"Your EasyOrder host link is ready. Keep this private: {host_short_url}"


def redact_timeline_message(message_text: str) -> str:
    redacted = message_text
    for pattern in TIMELINE_REDACTION_PATTERNS:
        redacted = pattern.sub("[redacted]", redacted)
    return redacted.strip()


def verify_signature(raw_body: bytes, signature_header: str | None, settings: Settings) -> None:
    if settings.skip_signature_verification:
        return

    if not settings.whatsapp_app_secret:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="WhatsApp app secret is not configured",
        )

    if not signature_header or not signature_header.startswith("sha256="):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing signature")

    expected_signature = hmac.new(
        settings.whatsapp_app_secret.encode("utf-8"),
        raw_body,
        hashlib.sha256,
    ).hexdigest()
    actual_signature = signature_header.removeprefix("sha256=")

    if not hmac.compare_digest(expected_signature, actual_signature):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid signature")


@router.get("/webhook")
async def verify_webhook(
    mode: str = Query(alias="hub.mode"),
    verify_token: str = Query(alias="hub.verify_token"),
    challenge: str = Query(alias="hub.challenge"),
    settings: Settings = Depends(get_settings),
) -> PlainTextResponse:
    if mode != "subscribe" or verify_token != settings.whatsapp_verify_token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid verify token")

    return PlainTextResponse(challenge)


@router.post("/webhook")
async def ingest_webhook(
    request: Request,
    x_hub_signature_256: str | None = Header(default=None),
    settings: Settings = Depends(get_settings),
    agent_service: IAgentService = Depends(get_agent_service),
    whatsapp_sender: IWhatsAppSender = Depends(get_whatsapp_sender),
    db: IDBAdapter = Depends(get_db_adapter),
    short_links: IShortLinkService = Depends(get_short_links),
) -> dict[str, object]:
    raw_body = await request.body()
    log_webhook_event(
        "whatsapp_webhook_received",
        bytes=len(raw_body),
        provider_mode=settings.whatsapp_provider_mode,
    )
    verify_signature(raw_body, x_hub_signature_256, settings)

    try:
        payload = WhatsAppWebhookPayload.model_validate_json(raw_body)
    except ValidationError as error:
        log_webhook_event("whatsapp_webhook_invalid_payload", error_count=len(error.errors()))
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Invalid WhatsApp webhook payload",
        ) from error

    incoming_messages = extract_incoming_messages(payload)
    tagged_messages = [message for message in incoming_messages if message.is_easyorder_tagged]
    log_webhook_event(
        "whatsapp_webhook_parsed",
        messages_seen=len(incoming_messages),
        tagged_messages=len(tagged_messages),
    )

    # --- Dedicated business chat: route untagged direct messages by intent ---
    planning_messages = list(tagged_messages)
    routed_intents: list[dict[str, str]] = []
    for message in incoming_messages:
        if message.is_easyorder_tagged:
            continue
        mode = classify_chat_mode(
            message,
            business_phone_number_id=settings.whatsapp_phone_number_id,
            business_chat_enabled=settings.whatsapp_business_chat_enabled,
        )
        if mode != ChatMode.BUSINESS_CHAT:
            continue
        routed = route_business_chat_message(message.message_text)
        log_webhook_event(
            "whatsapp_business_chat_routed",
            message_id=message.message_id,
            intent=routed.family,
            creates_session=routed.creates_session,
        )
        if routed.creates_session:
            planning_messages.append(message)
            continue
        if routed.reply_text:
            try:
                await whatsapp_sender.send_private_message(message.sender_id, routed.reply_text)
            except WhatsAppSendError as error:
                log_webhook_event(
                    "whatsapp_business_chat_reply_failed",
                    message_id=message.message_id,
                    intent=routed.family,
                    error=error,
                )
        routed_intents.append({"message_id": message.message_id, "intent": str(routed.family)})

    if not planning_messages and not routed_intents:
        log_webhook_event("whatsapp_webhook_ignored", reason="no_easyorder_mention")
        return {
            "status": "ignored",
            "reason": "no_easyorder_mention",
            "messages_seen": len(incoming_messages),
        }

    created_sessions = []
    duplicate_message_ids = []
    for message in planning_messages:
        existing_event = await db.get_session_event(
            message.message_id,
            EventType.WHATSAPP_TAGGED_MESSAGE,
        )
        if existing_event is not None:
            log_webhook_event(
                "whatsapp_webhook_duplicate",
                message_id=message.message_id,
                session_id=existing_event.session_id,
            )
            duplicate_message_ids.append(message.message_id)
            continue
        try:
            result = await agent_service.initialize_tagged_message(message)
        except AgentRejectedPromptError as error:
            log_webhook_event(
                "whatsapp_prompt_rejected",
                message_id=message.message_id,
                sender_id=message.sender_id,
            )
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Tagged message was rejected by input guardrails",
            ) from error
        session = result.session
        guest_link = build_session_link(
            settings.public_app_base_url,
            session.session_id,
            session.guest_token,
        )
        # --- Persist inbound event ---
        request_id = request.headers.get("x-request-id", "")
        await _try_insert_event(
            db,
            SessionEvent(
                session_id=session.session_id,
                event_type=EventType.WHATSAPP_INBOUND,
                message_text=redact_timeline_message(message.message_text),
                intent_label="start_session",
                message_id=message.message_id,
                sender_wa_id=message.sender_id,
                mode=settings.whatsapp_provider_mode,
                request_id=request_id,
            ),
        )
        await _try_insert_event(
            db,
            SessionEvent(
                session_id=session.session_id,
                event_type=EventType.SESSION_CREATED,
                intent_label="start_session",
                message_id=message.message_id,
                sender_wa_id=message.sender_id,
                mode=settings.whatsapp_provider_mode,
                request_id=request_id,
            ),
        )

        # --- Persist outbound links_sent event before attempting send ---
        # Record that links exist regardless of whether the WhatsApp send succeeds,
        # so the timeline is never missing LINKS_SENT due to a transient send failure.
        await _try_insert_event(
            db,
            SessionEvent(
                session_id=session.session_id,
                event_type=EventType.LINKS_SENT,
                mode=settings.whatsapp_provider_mode,
                request_id=request_id,
            ),
        )

        # --- Short-link aliases: handoff copy never carries raw tokenized URLs ---
        host_short_url = short_links.create_short_url(
            settings.public_app_base_url,
            build_session_path(session.session_id, result.host_token),
        )
        guest_short_url = short_links.create_short_url(
            settings.public_app_base_url,
            build_session_path(session.session_id, session.guest_token),
        )
        handoff = SessionHandoff(
            session_id=session.session_id,
            host_short_url=host_short_url,
            guest_short_url=guest_short_url,
        )

        try:
            if settings.whatsapp_provider_mode == "meta":
                log_webhook_event(
                    "whatsapp_handoff_sending",
                    message_id=message.message_id,
                    session_id=session.session_id,
                    recipient_id=message.sender_id,
                    channel="private",
                )
                await whatsapp_sender.send_session_handoff(message.sender_id, handoff)
            else:
                await whatsapp_sender.send_group_message(
                    message.phone_number_id,
                    build_group_session_message(guest_short_url),
                )
                await whatsapp_sender.send_private_message(
                    message.sender_id,
                    build_private_host_message(host_short_url),
                )
        except WhatsAppSendError as error:
            log_webhook_event(
                "whatsapp_handoff_failed",
                message_id=message.message_id,
                session_id=session.session_id,
                recipient_id=message.sender_id,
                error=error,
            )
            # Timeline records the failure so the UI never claims a delivery
            # that WhatsApp did not make; Meta's retry will attempt again.
            await _try_insert_event(
                db,
                SessionEvent(
                    session_id=session.session_id,
                    event_type=EventType.HANDOFF_FAILED,
                    message_id=message.message_id,
                    sender_wa_id=message.sender_id,
                    mode=settings.whatsapp_provider_mode,
                    request_id=request_id,
                ),
            )
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail="Session was created but WhatsApp handoff failed",
            ) from error
        await _try_insert_event(
            db,
            SessionEvent(
                session_id=session.session_id,
                event_type=EventType.HANDOFF_DELIVERED,
                message_id=message.message_id,
                sender_wa_id=message.sender_id,
                mode=settings.whatsapp_provider_mode,
                request_id=request_id,
            ),
        )
        # Recorded only after a successful handoff: a failed send returns 502
        # without a ledger entry, so Meta's retry can still deliver the links.
        await db.insert_session_event(
            SessionEvent(
                session_id=session.session_id,
                event_type=EventType.WHATSAPP_TAGGED_MESSAGE,
                message_id=message.message_id,
                sender_wa_id=message.sender_id,
                mode=settings.whatsapp_provider_mode,
                request_id=request_id,
            )
        )
        log_webhook_event(
            "whatsapp_session_created",
            message_id=message.message_id,
            session_id=session.session_id,
            recipient_id=message.sender_id,
        )
        created_sessions.append(
            {
                "session_id": session.session_id,
                "guest_link": guest_link,
                "guest_short_link": guest_short_url,
                "status": session.status,
            }
        )

    response: dict[str, object]
    if created_sessions:
        response = {"status": "created", "sessions": created_sessions}
    elif routed_intents:
        response = {"status": "routed"}
    else:
        response = {"status": "duplicate"}
    if routed_intents:
        response["intents"] = routed_intents
    if duplicate_message_ids:
        response["duplicates"] = duplicate_message_ids
    return response


async def _try_insert_event(db: IDBAdapter, event: SessionEvent) -> None:
    """Best-effort event persistence — log on failure, never raise."""
    try:
        await db.insert_session_event(event)
    except Exception:
        logger.exception("session_event_insert_failed session_id=%s", event.session_id)


def create_mock_agent_service() -> MockAgentService:
    return MockAgentService()


def create_agent_service(settings: Settings) -> IAgentService:
    if settings.swiggy_client_mode == "mock":
        return MockAgentService()
    return EasyOrderAgentService(
        db=InMemoryDBAdapter(),
        swiggy_client=create_swiggy_client(
            mode=settings.swiggy_client_mode,
            server_path=settings.swiggy_mcp_server_path,
            server_env=settings.swiggy_mcp_server_env,
        ),
    )
