import asyncio

from app.db.rls import build_rls_headers, encode_rls_headers, set_rls_headers


class FakeConnection:
    def __init__(self) -> None:
        self.calls: list[tuple[str, str]] = []

    async def execute(self, sql: str, value: str) -> None:
        self.calls.append((sql, value))


def test_build_rls_headers_omits_missing_tokens() -> None:
    assert build_rls_headers(guest_token="guest_public") == {"x-guest-token": "guest_public"}
    assert build_rls_headers(host_token="host_private") == {"x-host-token": "host_private"}


def test_encode_rls_headers_matches_postgres_request_headers_shape() -> None:
    encoded = encode_rls_headers(
        build_rls_headers(host_token="host_private", guest_token="guest_public")
    )

    assert encoded == '{"x-guest-token":"guest_public","x-host-token":"host_private"}'


def test_set_rls_headers_sets_transaction_local_request_headers() -> None:
    connection = FakeConnection()

    asyncio.run(set_rls_headers(connection, {"x-guest-token": "guest_public"}))

    assert connection.calls == [
        (
            "SELECT set_config('request.headers', $1, true)",
            '{"x-guest-token":"guest_public"}',
        )
    ]
