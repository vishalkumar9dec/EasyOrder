from __future__ import annotations

import hashlib
import hmac
import logging
from datetime import UTC, datetime

from fastapi import APIRouter, Depends, Header, HTTPException, Query, Request, status
from fastapi.responses import PlainTextResponse
from pydantic import ValidationError

from app.config import Settings, get_settings
from app.models.session import SessionEvent
from app.models.whatsapp import WhatsAppWebhookPayload, extract_incoming_messages
from app.services.agent import AgentRejectedPromptError, EasyOrderAgentService
from app.services.memory_db import InMemoryDBAdapter
from app.services.mock_agent import MockAgentService
from app.services.protocols import IAgentService, IDBAdapter, IWhatsAppSender
from app.services.swiggy_mcp import create_swiggy_client
from app.services.whatsapp_sender import WhatsAppSendError

router = APIRouter(prefix="/api/whatsapp", tags=["whatsapp"])
logger = logging.getLogger("easyorder.api")
terminal_logger = logging.getLogger("uvicorn.error")

TAGGED_MESSAGE_EVENT_TYPE = "whatsapp_tagged_message"


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


def build_session_link(base_url: str, session_id: str, token: str) -> str:
    return f"{base_url.rstrip('/')}/session/{session_id}?token={token}"


def build_group_session_message(guest_link: str) -> str:
    return f"EasyOrder is ready. Open the planning canvas: {guest_link}"


def build_private_host_message(host_link: str) -> str:
    return f"Your EasyOrder host link is ready. Keep this private: {host_link}"


def build_direct_user_session_message(guest_link: str, host_link: str) -> str:
    return (
        "EasyOrder is ready. Review and place the order from your private host link: "
        f"{host_link}\n\n"
        f"If you want others to review the planning canvas, share this guest link: {guest_link}"
    )


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
    db_adapter: IDBAdapter = Depends(get_db_adapter),
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

    if not tagged_messages:
        log_webhook_event("whatsapp_webhook_ignored", reason="no_easyorder_mention")
        return {
            "status": "ignored",
            "reason": "no_easyorder_mention",
            "messages_seen": len(incoming_messages),
        }

    created_sessions = []
    duplicate_message_ids = []
    for message in tagged_messages:
        existing_event = await db_adapter.get_session_event(
            message.message_id,
            TAGGED_MESSAGE_EVENT_TYPE,
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
        host_link = build_session_link(
            settings.public_app_base_url,
            session.session_id,
            result.host_token,
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
                await whatsapp_sender.send_private_message(
                    message.sender_id,
                    build_direct_user_session_message(guest_link, host_link),
                )
            else:
                await whatsapp_sender.send_group_message(
                    message.phone_number_id,
                    build_group_session_message(guest_link),
                )
                await whatsapp_sender.send_private_message(
                    message.sender_id,
                    build_private_host_message(host_link),
                )
        except WhatsAppSendError as error:
            log_webhook_event(
                "whatsapp_handoff_failed",
                message_id=message.message_id,
                session_id=session.session_id,
                recipient_id=message.sender_id,
                error=error,
            )
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail="Session was created but WhatsApp handoff failed",
            ) from error
        # Recorded only after a successful handoff: a failed send returns 502
        # without an event, so Meta's retry can still deliver the links.
        await db_adapter.insert_session_event(
            SessionEvent(
                message_id=message.message_id,
                event_type=TAGGED_MESSAGE_EVENT_TYPE,
                session_id=session.session_id,
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
                "status": session.status,
            }
        )

    if not created_sessions:
        return {
            "status": "duplicate",
            "duplicates": duplicate_message_ids,
        }

    response: dict[str, object] = {
        "status": "created",
        "sessions": created_sessions,
    }
    if duplicate_message_ids:
        response["duplicates"] = duplicate_message_ids
    return response


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
