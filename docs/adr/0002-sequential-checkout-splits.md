# ADR 0002: Sequential Checkout Splits for Food Restaurant and Grocery Carts

## Status
Accepted

## Context
EasyOrder allows groups to plan consolidated carts containing restaurant meals (via Swiggy Food) and groceries/beverages (via Swiggy Instamart). In the underlying Swiggy architecture, food deliveries and Instamart quick-commerce orders are dispatched from different source points (restaurants vs. dark stores) and are handled by separate rider segments.

Thus, a single atomic payment/checkout transaction covering both verticals is not supported by Swiggy APIs. In addition, Swiggy Food does not support a single Food order that combines items from multiple restaurants. A consolidated EasyOrder cart may therefore map to more than two Swiggy orders: one checkout per Food restaurant plus one Instamart checkout when grocery items exist.

## Decision
We decided to split the consolidated cart into distinct checkout payloads and guide the host through a **sequential checkout experience** on the PWA:
1. Food cart items are grouped by `restaurant_id`; each restaurant group creates one Food checkout payload.
2. Instamart items create a separate Instamart checkout payload.
3. The host sees every required checkout step before starting OAuth/payment, including restaurant/store labels and subtotals.
4. The PWA maps all checkout confirmations to the singular EasyOrder Session ID to track collective status.

## Consequences
* **Pros:**
  * Aligns perfectly with Swiggy’s production backend infrastructure, eliminating custom cart aggregation risks.
  * Makes the real fulfillment source visible to the host and group before payment.
  * Allows host to check out whichever part of the order is ready first (e.g. one restaurant order is booked while drinks selection is still being finalized).
* **Cons:**
  * Introduces checkout friction proportional to the number of selected restaurants plus Instamart.
  * If one checkout succeeds but a later one fails (e.g. out of stock or host abandons), the host has a partially completed group order. The PWA must show a prominent notice to resume or cancel remaining checkout steps.
  * The agent and UI should prefer single-restaurant Food recommendations when they satisfy the group constraints, because each extra restaurant adds operational friction.
