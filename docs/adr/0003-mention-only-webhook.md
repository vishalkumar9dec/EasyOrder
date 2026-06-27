# ADR 0003: Mention-Only Listening for the WhatsApp Group Bot

## Status
Accepted

## Context
EasyOrder functions within group chat environments on WhatsApp. If the bot listens to and reads all messages in the group, this would:
1. Compromise user privacy and data security.
2. Incur high token processing and execution costs by parsing irrelevant messages.
3. Violate WhatsApp Business policy guidelines regarding data scanning.

## Decision
We decided to configure the WhatsApp webhook to ignore all group messages except those where the bot is explicitly tagged (e.g. `@EasyOrder`). 

If a message does not contain the `@EasyOrder` tag, the webhook returns a 200 OK instantly and does not log, process, or forward the message body.

## Consequences
* **Pros:**
  * Strict privacy protection: users know the bot only processes what they explicitly send to it.
  * Significantly reduces LLM processing costs and prevents unwanted webhooks from overloading the server.
  * Easy compliance with WhatsApp developer terms.
* **Cons:**
  * The bot cannot proactively offer recommendations based on ambient chat context (e.g., if a user says "I am hungry" without tagging the bot). All proactive invitations must be initiated by external crons using templated messages.
