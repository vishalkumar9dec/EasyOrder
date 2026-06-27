# ADR 0002: Sequential Checkout Splits for Food and Grocery Carts

## Status
Accepted

## Context
EasyOrder allows groups to plan consolidated carts containing restaurant meals (via Swiggy Food) and groceries/beverages (via Swiggy Instamart). In the underlying Swiggy architecture, food deliveries and Instamart quick-commerce orders are dispatched from different source points (restaurants vs. dark stores) and are handled by separate rider segments. 

Thus, a single atomic payment/checkout transaction covering both verticals is not supported by Swiggy APIs.

## Decision
We decided to split the consolidated cart into two distinct checkout payloads and guide the host through a **sequential checkout experience** on the PWA:
1. First, the host authorizes and completes the payment for the Food cart.
2. Second, the PWA automatically transitions to checkout the Instamart cart.
3. The PWA maps both checkout confirmations to the singular EasyOrder Session ID to track collective status.

## Consequences
* **Pros:**
  * Aligns perfectly with Swiggy’s production backend infrastructure, eliminating custom cart aggregation risks.
  * Allows host to check out whichever part of the order is ready first (e.g. food is booked while drinks selection is still being finalized).
* **Cons:**
  * Introduces minor checkout friction (host has to swipe/confirm payment twice).
  * If the first checkout succeeds but the second fails (e.g. out of stock or host abandons), the host has a partially completed group order. The PWA must show a prominent notice to resume or cancel.
