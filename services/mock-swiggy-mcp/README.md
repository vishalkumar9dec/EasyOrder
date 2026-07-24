# mock-swiggy-mcp

A standalone mock of Swiggy's MCP server, independent of the EasyOrder
backend. In a real deployment, Swiggy would host an MCP endpoint and hand
EasyOrder a URL plus credentials; EasyOrder would connect as an MCP client.
This service exists so that integration can be built and tested locally
before real Swiggy partner access is available — swap `SWIGGY_MCP_SERVER_URL`
for the real endpoint later, with no client-side code changes.

Built with the official [`mcp`](https://modelcontextprotocol.io) Python SDK,
served over Streamable HTTP.

## Run locally

```bash
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt -r requirements-dev.txt
MOCK_MCP_AUTH_TOKEN=dev-token .venv/bin/python app/server.py
# serves http://127.0.0.1:9100/mcp
```

Or via the repo Makefile: `make mock-mcp-install`, then `make mock-mcp-up`.

## Run via Docker

```bash
docker build -t mock-swiggy-mcp .
docker run --rm -p 9100:9100 -e MOCK_MCP_AUTH_TOKEN=dev-token mock-swiggy-mcp
```

## Configuration

| Env var | Default | Purpose |
|---|---|---|
| `MOCK_MCP_HOST` | `127.0.0.1` | Bind host |
| `MOCK_MCP_PORT` | `9100` | Bind port |
| `MOCK_MCP_AUTH_TOKEN` | (unset) | If set, requests must send `Authorization: Bearer <token>` |

Point EasyOrder's backend at it via `SWIGGY_CLIENT_MODE=mcp`,
`SWIGGY_MCP_SERVER_URL=http://localhost:9100/mcp`,
`SWIGGY_MCP_AUTH_TOKEN=dev-token` (see `src/backend/.env.example`).

## Tools

Restaurant discovery/detail: `get_restaurants`, `get_restaurant`,
`search_restaurants`, `get_restaurant_menu`.
Instamart: `search_instamart`, `get_substitute_items`.
Checkout/order lifecycle: `exchange_oauth_code`, `create_cart`, `place_order`,
`get_order_history`, `get_current_order`, `get_delivery_update`.

Order state is in-memory and process-local — restarting the server clears
order history. `get_current_order`/`get_delivery_update` progress a placed
order through `placed → preparing → out_for_delivery → delivered` once per
poll, deterministically (not on a timer), so demos and tests aren't racy.

## Tests

```bash
.venv/bin/pytest
```

Spawns the real server as a subprocess per test and drives it with the
official MCP client SDK — the same round trip EasyOrder's backend uses.
