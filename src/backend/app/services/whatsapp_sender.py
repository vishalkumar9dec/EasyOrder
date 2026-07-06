"""Outbound WhatsApp sender implementations."""

from __future__ import annotations

import asyncio
import json
import urllib.error
import urllib.request
from dataclasses import dataclass

from pydantic import BaseModel, Field


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


class MockWhatsAppSender:
    """In-memory sender used by local development and automated tests."""

    def __init__(self) -> None:
        self.sent_messages: list[OutgoingWhatsAppMessage] = []
        self.template_placeholders: list[TemplateMessagePlaceholder] = []

    async def send_group_message(self, group_id: str, text: str) -> None:
        self.sent_messages.append(
            OutgoingWhatsAppMessage(recipient_id=group_id, text=text, channel="group")
        )

    async def send_private_message(self, recipient_id: str, text: str) -> None:
        self.sent_messages.append(
            OutgoingWhatsAppMessage(recipient_id=recipient_id, text=text, channel="private")
        )

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
    ) -> None:
        if not access_token:
            raise ValueError("Meta WhatsApp access token is required")
        if not phone_number_id:
            raise ValueError("Meta WhatsApp phone number id is required")
        self.access_token = access_token
        self.phone_number_id = phone_number_id
        self.api_version = api_version

    async def send_group_message(self, group_id: str, text: str) -> None:
        await asyncio.to_thread(self._send_text_message, group_id, text)

    async def send_private_message(self, recipient_id: str, text: str) -> None:
        await asyncio.to_thread(self._send_text_message, recipient_id, text)

    def _send_text_message(self, recipient_id: str, text: str) -> None:
        url = (
            f"https://graph.facebook.com/{self.api_version}/"
            f"{self.phone_number_id}/messages"
        )
        payload = {
            "messaging_product": "whatsapp",
            "to": recipient_id,
            "type": "text",
            "text": {"preview_url": False, "body": text},
        }
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
) -> MockWhatsAppSender | MetaCloudWhatsAppSender:
    if provider_mode == "meta":
        return MetaCloudWhatsAppSender(
            access_token=access_token,
            phone_number_id=phone_number_id,
            api_version=api_version,
        )
    return MockWhatsAppSender()
