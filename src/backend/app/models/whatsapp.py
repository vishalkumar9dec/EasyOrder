"""Pydantic models for Meta/WhatsApp Cloud API webhook payloads.

These models mirror the nested structure Meta sends on incoming messages.
Only the fields EasyOrder needs are parsed; the rest is ignored via
``model_config = {"extra": "ignore"}``.

See: https://developers.facebook.com/docs/whatsapp/cloud-api/webhooks/payload-examples
"""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field

# Innermost payload layers


class WhatsAppText(BaseModel):
    """The text body of a WhatsApp message."""

    body: str

    model_config = ConfigDict(extra="ignore")


class WhatsAppMessage(BaseModel):
    """A single message inside a WhatsApp webhook change value."""

    from_: str = Field(alias="from")
    id: str
    timestamp: str
    text: WhatsAppText | None = None
    type: str = "text"

    model_config = ConfigDict(extra="ignore", populate_by_name=True)


class WhatsAppContact(BaseModel):
    """Sender contact metadata."""

    wa_id: str

    model_config = ConfigDict(extra="ignore")


class WhatsAppMetadata(BaseModel):
    """Business account metadata."""

    display_phone_number: str
    phone_number_id: str

    model_config = ConfigDict(extra="ignore")


class WhatsAppValue(BaseModel):
    """The 'value' payload inside a webhook change entry."""

    messaging_product: str = "whatsapp"
    metadata: WhatsAppMetadata
    contacts: list[WhatsAppContact] | None = None
    messages: list[WhatsAppMessage] | None = None

    model_config = ConfigDict(extra="ignore")


class WhatsAppChange(BaseModel):
    """A single change entry in the webhook."""

    field: str = "messages"
    value: WhatsAppValue

    model_config = ConfigDict(extra="ignore")


class WhatsAppEntry(BaseModel):
    """A single entry in the top-level webhook payload."""

    id: str
    changes: list[WhatsAppChange]

    model_config = ConfigDict(extra="ignore")


# Top-level webhook payload


class WhatsAppWebhookPayload(BaseModel):
    """Top-level structure Meta POSTs to ``/api/whatsapp/webhook``.

    Example (simplified)::

        {
            "object": "whatsapp_business_account",
            "entry": [{
                "id": "BIZ_ACCOUNT_ID",
                "changes": [{
                    "field": "messages",
                    "value": {
                        "messaging_product": "whatsapp",
                        "metadata": {
                            "display_phone_number": "15551234567",
                            "phone_number_id": "PH_ID",
                        },
                        "contacts": [{"wa_id": "919988776655"}],
                        "messages": [{
                            "from": "919988776655",
                            "id": "wamid.xyz",
                            "timestamp": "1782489000",
                            "type": "text",
                            "text": {"body": "@EasyOrder need biryani for 6"}
                        }]
                    }
                }]
            }]
        }
    """

    object: str  # always "whatsapp_business_account"
    entry: list[WhatsAppEntry]

    model_config = ConfigDict(extra="ignore")


# Internal domain model (parsed from webhook)


class IncomingMessage(BaseModel):
    """Flattened, internal representation of a single incoming WhatsApp message.

    Built by extracting the useful fields from the deeply-nested Meta payload.
    This is the model the rest of EasyOrder operates on.
    """

    sender_id: str
    message_id: str
    message_text: str
    phone_number_id: str
    timestamp: str
    is_easyorder_tagged: bool = False


def extract_incoming_messages(payload: WhatsAppWebhookPayload) -> list[IncomingMessage]:
    """Flatten useful text messages from a Meta webhook payload."""
    incoming_messages: list[IncomingMessage] = []

    for entry in payload.entry:
        for change in entry.changes:
            messages = change.value.messages or []
            for message in messages:
                if message.type != "text" or message.text is None:
                    continue

                message_text = message.text.body
                incoming_messages.append(
                    IncomingMessage(
                        sender_id=message.from_,
                        message_id=message.id,
                        message_text=message_text,
                        phone_number_id=change.value.metadata.phone_number_id,
                        timestamp=message.timestamp,
                        is_easyorder_tagged="@easyorder" in message_text.lower(),
                    )
                )

    return incoming_messages
