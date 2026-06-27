from __future__ import annotations

import hashlib
import hmac

from fastapi import APIRouter, Depends, Header, HTTPException, Query, Request, status
from fastapi.responses import PlainTextResponse
from pydantic import ValidationError

from app.config import Settings, get_settings
from app.models.whatsapp import WhatsAppWebhookPayload, extract_incoming_messages
from app.services.mock_agent import InMemorySessionStore, MockAgentService
from app.services.protocols import IAgentService

router = APIRouter(prefix="/api/whatsapp", tags=["whatsapp"])


def get_agent_service(request: Request) -> IAgentService:
    return request.app.state.agent_service


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
) -> dict[str, object]:
    raw_body = await request.body()
    verify_signature(raw_body, x_hub_signature_256, settings)

    try:
        payload = WhatsAppWebhookPayload.model_validate_json(raw_body)
    except ValidationError as error:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Invalid WhatsApp webhook payload",
        ) from error

    incoming_messages = extract_incoming_messages(payload)
    tagged_messages = [message for message in incoming_messages if message.is_easyorder_tagged]

    if not tagged_messages:
        return {
            "status": "ignored",
            "reason": "no_easyorder_mention",
            "messages_seen": len(incoming_messages),
        }

    created_sessions = []
    for message in tagged_messages:
        session = await agent_service.handle_tagged_message(message)
        created_sessions.append(
            {
                "session_id": session.session_id,
                "guest_link": f"/session/{session.session_id}?token={session.guest_token}",
                "status": session.status,
            }
        )

    return {
        "status": "created",
        "sessions": created_sessions,
    }


def create_mock_agent_service() -> MockAgentService:
    return MockAgentService(InMemorySessionStore())
