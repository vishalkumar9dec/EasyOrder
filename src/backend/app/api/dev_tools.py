"""Local-development helpers. Fail closed outside local mock setups."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Request, status

from app.config import Settings, get_settings
from app.services.whatsapp_sender import MockWhatsAppSender

router = APIRouter(prefix="/api/dev", tags=["dev"])


@router.get("/whatsapp-outbox")
async def whatsapp_outbox(
    request: Request,
    settings: Settings = Depends(get_settings),
) -> dict[str, object]:
    """Expose mock-captured outbound WhatsApp messages for local testing.

    Lets the OTP login flow be exercised in a browser without a handset.
    Available only when APP_ENV=local AND the mock sender is active — any
    other configuration 404s so this can never leak in meta/live setups.
    """
    sender = request.app.state.whatsapp_sender
    if settings.app_env != "local" or not isinstance(sender, MockWhatsAppSender):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Not found")
    return {
        "messages": [
            {"recipient_id": m.recipient_id, "channel": m.channel, "text": m.text}
            for m in sender.sent_messages[-20:]
        ]
    }
