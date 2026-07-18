"""In-process sliding-window rate limiting for abuse-sensitive endpoints.

Used to throttle OTP-request traffic (per phone and per client IP) so the
login endpoint cannot be turned into a WhatsApp-message cannon or used to
reset the verify attempt counter. The state is process-local; when the backend
runs more than one instance this must move to a shared store (Redis/Postgres)
to be effective across replicas. See docs/production-readiness.md.
"""

from __future__ import annotations

import time
from collections import defaultdict, deque
from collections.abc import Callable


class SlidingWindowRateLimiter:
    """Allows at most ``max_events`` per key within a rolling ``window_seconds``."""

    def __init__(
        self,
        max_events: int,
        window_seconds: float,
        clock: Callable[[], float] = time.monotonic,
    ) -> None:
        self._max = max_events
        self._window = window_seconds
        self._clock = clock
        self._events: dict[str, deque[float]] = defaultdict(deque)

    def allow(self, key: str) -> bool:
        """Record an event and return True if it is within the limit."""
        now = self._clock()
        cutoff = now - self._window
        events = self._events[key]
        while events and events[0] <= cutoff:
            events.popleft()
        if len(events) >= self._max:
            return False
        events.append(now)
        return True

    def reset(self) -> None:
        self._events.clear()


class OtpRateLimiter:
    """Composite per-phone and per-IP limiter for the OTP request endpoint."""

    def __init__(
        self,
        *,
        per_phone_max: int = 3,
        per_phone_window: float = 600.0,
        per_ip_max: int = 30,
        per_ip_window: float = 600.0,
        clock: Callable[[], float] = time.monotonic,
    ) -> None:
        self._phone = SlidingWindowRateLimiter(per_phone_max, per_phone_window, clock)
        self._ip = SlidingWindowRateLimiter(per_ip_max, per_ip_window, clock)

    def allow(self, wa_id: str, client_ip: str | None) -> bool:
        # Check the phone bucket first; if it is exhausted, do not consume from
        # the IP bucket (so one hot phone can't drain a shared-NAT IP's quota).
        if not self._phone.allow(f"phone:{wa_id}"):
            return False
        return self._ip.allow(f"ip:{client_ip or 'unknown'}")
