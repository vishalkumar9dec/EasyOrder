"""Outbound WhatsApp sender implementations."""

from __future__ import annotations

import asyncio
import json
import logging
import urllib.error
import urllib.request
from dataclasses import dataclass

from pydantic import BaseModel, Field

logger = logging.getLogger("easyorder.whatsapp")


class WhatsAppSendError(RuntimeError):
    """Raised when an outbound WhatsApp message cannot be delivered."""


class OutgoingWhatsAppMessage(BaseModel):
    """Captured outbound WhatsApp message for tests and local demos."""

    recipient_id: str
    text: str
    channel: str = Field(pattern="^(group|private)$")


@dataclass(frozen=True)
class TemplateMessagePlaceholder:
    """Deferred proactive template-message contract for later integration work."""

    template_name: str
    recipient_id: str
    parameters: dict[str, str]
    enabled: bool = False


@dataclass(frozen=True)
class SessionHandoff:
    """Session handoff content rendered by capability-aware senders.

    Both URLs are short-link aliases; raw tokenized session URLs must
    never appear in handoff copy (task 10.2).
    """

    session_id: str
    host_short_url: str
    guest_short_url: str
    cta_text: str = "Review order"
    guest_cta_text: str = "Open planning canvas"

    @property
    def host_body_text(self) -> str:
        return (
            "EasyOrder is ready. Tap the button to review and place the order "
            "from your private host view."
        )

    @property
    def guest_body_text(self) -> str:
        # The guest short link stays in the body so it can be copied or
        # forwarded to the group; the button opens the same URL.
        return f"Share the planning canvas with the group: {self.guest_short_url}"

    @property
    def fallback_text(self) -> str:
        return (
            f"EasyOrder is ready. Review and place the order: {self.host_short_url}\n\n"
            f"Share the planning canvas with the group: {self.guest_short_url}"
        )


def build_cta_url_payload(
    recipient_id: str,
    *,
    body_text: str,
    display_text: str,
    url: str,
) -> dict:
    """Interactive CTA-URL message: no template approval needed, valid in the
    24h customer-service window that the inbound message just opened."""
    return {
        "messaging_product": "whatsapp",
        "to": recipient_id,
        "type": "interactive",
        "interactive": {
            "type": "cta_url",
            "body": {"text": body_text},
            "action": {
                "name": "cta_url",
                "parameters": {"display_text": display_text, "url": url},
            },
        },
    }


def build_cta_handoff_payloads(recipient_id: str, handoff: SessionHandoff) -> list[dict]:
    """Two CTA messages: WhatsApp allows only one URL button per interactive
    message, so host review and guest share each get their own button."""
    return [
        build_cta_url_payload(
            recipient_id,
            body_text=handoff.host_body_text,
            display_text=handoff.cta_text,
            url=handoff.host_short_url,
        ),
        build_cta_url_payload(
            recipient_id,
            body_text=handoff.guest_body_text,
            display_text=handoff.guest_cta_text,
            url=handoff.guest_short_url,
        ),
    ]


def build_template_handoff_payload(
    recipient_id: str,
    handoff: SessionHandoff,
    *,
    template_name: str,
    template_language: str,
) -> dict:
    """Approved-template handoff: one message with two URL buttons.

    Contract documented in docs/runbooks/whatsapp-handoff-templates.md:
    body variable {{1}} = guest short URL, URL button 0 = host short URL
    (Review order), URL button 1 = guest short URL (Open planning canvas).
    The approved base URLs stay token-free; parameters supply the links.
    """
    return {
        "messaging_product": "whatsapp",
        "to": recipient_id,
        "type": "template",
        "template": {
            "name": template_name,
            "language": {"code": template_language},
            "components": [
                {
                    "type": "body",
                    "parameters": [{"type": "text", "text": handoff.guest_short_url}],
                },
                {
                    "type": "button",
                    "sub_type": "url",
                    "index": "0",
                    "parameters": [{"type": "text", "text": handoff.host_short_url}],
                },
                {
                    "type": "button",
                    "sub_type": "url",
                    "index": "1",
                    "parameters": [{"type": "text", "text": handoff.guest_short_url}],
                },
            ],
        },
    }


class MockWhatsAppSender:
    """In-memory sender used by local development and automated tests."""

    def __init__(self) -> None:
        self.sent_messages: list[OutgoingWhatsAppMessage] = []
        self.sent_handoffs: list[tuple[str, SessionHandoff]] = []
        self.template_placeholders: list[TemplateMessagePlaceholder] = []

    async def send_group_message(self, group_id: str, text: str) -> None:
        self.sent_messages.append(
            OutgoingWhatsAppMessage(recipient_id=group_id, text=text, channel="group")
        )

    async def send_private_message(self, recipient_id: str, text: str) -> None:
        self.sent_messages.append(
            OutgoingWhatsAppMessage(recipient_id=recipient_id, text=text, channel="private")
        )

    async def send_session_handoff(self, recipient_id: str, handoff: SessionHandoff) -> None:
        """Capture the handoff and its fallback text rendering for assertions."""
        self.sent_handoffs.append((recipient_id, handoff))
        await self.send_private_message(recipient_id, handoff.fallback_text)

    def create_template_placeholder(
        self,
        template_name: str,
        recipient_id: str,
        parameters: dict[str, str] | None = None,
    ) -> TemplateMessagePlaceholder:
        placeholder = TemplateMessagePlaceholder(
            template_name=template_name,
            recipient_id=recipient_id,
            parameters=parameters or {},
        )
        self.template_placeholders.append(placeholder)
        return placeholder


class MetaCloudWhatsAppSender:
    """Meta Cloud API sender for sandbox and production-compatible WhatsApp sends."""

    def __init__(
        self,
        *,
        access_token: str,
        phone_number_id: str,
        api_version: str = "v20.0",
        handoff_template_name: str = "",
        handoff_template_language: str = "en",
    ) -> None:
        if not access_token:
            raise ValueError("Meta WhatsApp access token is required")
        if not phone_number_id:
            raise ValueError("Meta WhatsApp phone number id is required")
        self.access_token = access_token
        self.phone_number_id = phone_number_id
        self.api_version = api_version
        self.handoff_template_name = handoff_template_name
        self.handoff_template_language = handoff_template_language

    async def send_group_message(self, group_id: str, text: str) -> None:
        await asyncio.to_thread(self._post_message_payload, self._text_payload(group_id, text))

    async def send_private_message(self, recipient_id: str, text: str) -> None:
        await asyncio.to_thread(self._post_message_payload, self._text_payload(recipient_id, text))

    async def send_session_handoff(self, recipient_id: str, handoff: SessionHandoff) -> None:
        """Send the richest supported handoff, degrading to plain text.

        Order: approved template (one message, two URL buttons) when
        configured; otherwise two interactive CTA messages (WhatsApp allows
        one URL button each). Any Graph rejection degrades to one concise
        short-link text message carrying both links.
        """
        if self.handoff_template_name:
            payloads = [
                build_template_handoff_payload(
                    recipient_id,
                    handoff,
                    template_name=self.handoff_template_name,
                    template_language=self.handoff_template_language,
                )
            ]
        else:
            payloads = build_cta_handoff_payloads(recipient_id, handoff)

        try:
            for payload in payloads:
                await asyncio.to_thread(self._post_message_payload, payload)
        except WhatsAppSendError as error:
            logger.warning(
                "whatsapp_handoff_rich_payload_failed session_id=%s payload_type=%s error=%s",
                handoff.session_id,
                payload.get("type"),
                error,
            )
            await self.send_private_message(recipient_id, handoff.fallback_text)

    def _text_payload(self, recipient_id: str, text: str) -> dict:
        return {
            "messaging_product": "whatsapp",
            "to": recipient_id,
            "type": "text",
            "text": {"preview_url": False, "body": text},
        }

    def _send_text_message(self, recipient_id: str, text: str) -> None:
        self._post_message_payload(self._text_payload(recipient_id, text))

    def _post_message_payload(self, payload: dict) -> None:
        url = (
            f"https://graph.facebook.com/{self.api_version}/"
            f"{self.phone_number_id}/messages"
        )
        request = urllib.request.Request(
            url,
            data=json.dumps(payload).encode("utf-8"),
            headers={
                "Authorization": f"Bearer {self.access_token}",
                "Content-Type": "application/json",
            },
            method="POST",
        )
        try:
            with urllib.request.urlopen(request, timeout=10) as response:
                if response.status >= 400:
                    raise WhatsAppSendError(f"Meta WhatsApp send failed with {response.status}")
        except urllib.error.HTTPError as error:
            body = error.read().decode("utf-8", errors="replace").strip()
            detail = f"Meta WhatsApp send failed with {error.code}"
            if body:
                detail = f"{detail}: {body[:1000]}"
            raise WhatsAppSendError(detail) from error
        except urllib.error.URLError as error:
            raise WhatsAppSendError("Meta WhatsApp send failed") from error


def create_whatsapp_sender(
    *,
    provider_mode: str,
    access_token: str,
    phone_number_id: str,
    api_version: str,
    handoff_template_name: str = "",
    handoff_template_language: str = "en",
) -> MockWhatsAppSender | MetaCloudWhatsAppSender:
    if provider_mode == "meta":
        return MetaCloudWhatsAppSender(
            access_token=access_token,
            phone_number_id=phone_number_id,
            api_version=api_version,
            handoff_template_name=handoff_template_name,
            handoff_template_language=handoff_template_language,
        )
    return MockWhatsAppSender()
