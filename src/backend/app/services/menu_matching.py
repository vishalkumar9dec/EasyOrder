"""Shared name-matching helpers for restaurant/dish resolution.

Used by both ``MockSwiggyMcpClient`` (matches directly against local fixture
data) and ``SwiggyMcpClient`` (matches against normalized MCP tool
responses) so restaurant-by-name and dish-name-within-menu lookups behave
identically regardless of which Swiggy client is active.
"""

from __future__ import annotations

import re
from collections.abc import Sequence
from typing import Any

_TOKEN_PATTERN = re.compile(r"[a-z0-9]+")


def normalize_tokens(text: str) -> list[str]:
    return _TOKEN_PATTERN.findall(text.lower())


def find_restaurant_by_name(
    restaurants: Sequence[dict[str, Any]],
    name: str,
) -> dict[str, Any] | None:
    """Case-insensitive substring match; None when nothing matches."""
    query = name.strip().lower()
    if not query:
        return None
    for restaurant in restaurants:
        if query in str(restaurant["name"]).lower():
            return dict(restaurant)
    return None


def match_menu_items(
    menu: Sequence[dict[str, Any]],
    dish_names: Sequence[str],
) -> list[dict[str, Any]]:
    """Return menu items matching each dish name, in request order.

    A dish name matches a menu item when every significant token of the
    dish name appears in the item's normalized name. Unmatched dish names
    are simply omitted from the result.
    """
    matched: list[dict[str, Any]] = []
    for dish_name in dish_names:
        query_tokens = normalize_tokens(dish_name)
        if not query_tokens:
            continue
        for item in menu:
            item_tokens = set(normalize_tokens(str(item["name"])))
            if all(token in item_tokens for token in query_tokens):
                matched.append(dict(item))
                break
    return matched
