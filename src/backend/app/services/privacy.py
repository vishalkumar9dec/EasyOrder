"""Self-service data erasure for EasyOrder's dedicated business chat.

EasyOrder stores phone numbers and order history (DPDP Act "personal data").
This is the user-facing erasure path: a WhatsApp message deletes every
session, cart, and timeline event tied to the sender's own wa_id. Requires
one message containing both a deletion trigger phrase and "confirm" (see
intent_router.py), so a single ambiguous message can never delete data by
accident — the first reply is always the warning, never the deletion itself.
"""

from __future__ import annotations

from app.services.protocols import IDBAdapter

DELETION_CONFIRMED_REPLY_TEMPLATE = (
    "Done — deleted {count} EasyOrder session(s) and all associated cart "
    "and order history for your number. This cannot be undone."
)
DELETION_NOTHING_TO_DELETE_REPLY = (
    "You don't have any EasyOrder data stored, so there's nothing to delete."
)


async def answer_data_deletion_request(
    db: IDBAdapter,
    *,
    wa_id: str,
    confirmed: bool,
    warning_reply: str,
) -> str:
    """Return the reply for a data-deletion request, deleting data only when confirmed."""
    if not confirmed:
        return warning_reply

    deleted_count = await db.delete_sessions_for_host(wa_id)
    if deleted_count == 0:
        return DELETION_NOTHING_TO_DELETE_REPLY
    return DELETION_CONFIRMED_REPLY_TEMPLATE.format(count=deleted_count)
