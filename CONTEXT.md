# EasyOrder Domain Glossary

This document outlines the canonical vocabulary for the EasyOrder system. It is strictly limited to domain terms and is completely devoid of implementation details.

## Domain Glossary

* **Session:** A single, active planning event representing a group's food coordination journey. A session starts in the WhatsApp group chat, transitions to the collaborative canvas, and completes when the checkout order is created or when the session expires.
* **Host:** The user who initiates the EasyOrder session in a WhatsApp group chat. The host has exclusive permission to trigger checkouts, authenticate via Swiggy OAuth, and complete the final payment.
* **Guest:** A group member who joins an active planning session via the shared canvas link. Guests can add, remove, or modify items in the cart but cannot trigger the checkout or view host-specific checkout credentials.
* **Consolidated Cart:** The combined planning view of items from Swiggy Food and Swiggy Instamart. The consolidated view is not necessarily one Swiggy order.
* **Source Attribution:** The vendor context attached to every cart item. Food items carry restaurant identity; Instamart items carry brand/source context when available.
* **Planning Canvas:** The shared visual interface where the host and guests collaboratively view, add, and adjust items in the consolidated cart.
* **Budget Limit:** The maximum total financial allowance set by the host during session initialization. The system warns the group if additions exceed this threshold.
* **Dietary Tag:** Metadata (e.g., VEG, NON-VEG) associated with items and menus, used to split carts and verify split totals.
* **Degraded State:** A session state where one of Swiggy's underlying verticals (Food or Instamart) is unavailable or times out, resulting in a partial planning experience (e.g., food recommendation is active but cold drinks are disabled).
* **Checkout Split:** The division of the consolidated cart into the Swiggy orders that can actually be placed: one order per Food restaurant plus one Instamart order when grocery items exist.
