from app.services.rate_limit import OtpRateLimiter, SlidingWindowRateLimiter


class FakeClock:
    def __init__(self) -> None:
        self.now = 0.0

    def __call__(self) -> float:
        return self.now


def test_sliding_window_allows_up_to_max_then_blocks() -> None:
    clock = FakeClock()
    limiter = SlidingWindowRateLimiter(max_events=2, window_seconds=60, clock=clock)

    assert limiter.allow("k") is True
    assert limiter.allow("k") is True
    assert limiter.allow("k") is False  # third within window is blocked


def test_sliding_window_recovers_after_window_elapses() -> None:
    clock = FakeClock()
    limiter = SlidingWindowRateLimiter(max_events=1, window_seconds=60, clock=clock)

    assert limiter.allow("k") is True
    assert limiter.allow("k") is False
    clock.now += 61
    assert limiter.allow("k") is True  # window slid past the first event


def test_sliding_window_keys_are_independent() -> None:
    clock = FakeClock()
    limiter = SlidingWindowRateLimiter(max_events=1, window_seconds=60, clock=clock)

    assert limiter.allow("a") is True
    assert limiter.allow("b") is True  # different key has its own budget


def test_otp_limiter_blocks_on_phone_or_ip_budget() -> None:
    clock = FakeClock()
    limiter = OtpRateLimiter(
        per_phone_max=5,
        per_phone_window=600,
        per_ip_max=2,
        per_ip_window=600,
        clock=clock,
    )

    # Distinct phones, same IP: the IP budget (2) is the binding constraint.
    assert limiter.allow("91999", "1.2.3.4") is True
    assert limiter.allow("91888", "1.2.3.4") is True
    assert limiter.allow("91777", "1.2.3.4") is False

    # A phone that is over its own budget is blocked before touching the IP bucket.
    phone_limiter = OtpRateLimiter(per_phone_max=1, per_ip_max=100, clock=clock)
    assert phone_limiter.allow("91999", "5.6.7.8") is True
    assert phone_limiter.allow("91999", "5.6.7.8") is False
