"""Short-link aliases for tokenized session URLs.

WhatsApp handoff copy must never display raw tokenized session URLs
(task 10.2). Instead, an opaque short code maps server-side to the
tokenized session path; the redirect endpoint resolves it on click.
Codes carry no token material, so leaking a message body never leaks
a token directly — the code is only useful while the mapping exists.
"""

from __future__ import annotations

import secrets

SHORT_LINK_PATH_PREFIX = "/api/r"


class InMemoryShortLinkService:
    """Process-local short-link store, matching in-memory session scope.

    Mappings live exactly as long as the sessions they point at (both
    reset on backend restart in mock mode), so a stale code can never
    outlive its session.
    """

    def __init__(self, *, code_bytes: int = 6) -> None:
        self._code_bytes = code_bytes
        self._paths_by_code: dict[str, str] = {}
        self._codes_by_path: dict[str, str] = {}

    def create(self, target_path: str) -> str:
        """Return a short code for a relative target path, reusing existing codes."""
        if not target_path.startswith("/"):
            raise ValueError("Short-link targets must be relative paths")
        if existing := self._codes_by_path.get(target_path):
            return existing
        code = secrets.token_urlsafe(self._code_bytes)
        while code in self._paths_by_code:
            code = secrets.token_urlsafe(self._code_bytes)
        self._paths_by_code[code] = target_path
        self._codes_by_path[target_path] = code
        return code

    def resolve(self, code: str) -> str | None:
        """Return the target path for a code, or None when unknown."""
        return self._paths_by_code.get(code)

    def create_short_url(self, base_url: str, target_path: str) -> str:
        """Return the absolute short URL for a relative target path."""
        code = self.create(target_path)
        return f"{base_url.rstrip('/')}{SHORT_LINK_PATH_PREFIX}/{code}"
