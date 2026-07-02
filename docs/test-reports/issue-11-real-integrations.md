# Issue #11 Real Integration Boundary Test Report

Date: 2026-07-02
Branch: `codex/issue-11-real-integrations`

## Scope

Issue [#11](https://github.com/vishalkumar9dec/EasyOrder/issues/11) implements
the real integration boundary slice for Tasks 8.1 and 8.2:

- Add a selectable `SwiggyMcpClient` behind `SWIGGY_CLIENT_MODE=mcp`.
- Add MCP stdio runner configuration through `SWIGGY_MCP_SERVER_PATH` and
  `SWIGGY_MCP_SERVER_ENV`.
- Normalize real Swiggy Food, Instamart, OAuth, checkout, menu, and substitute
  responses into the same contract as the mock client.
- Map MCP tool and configuration failures to application exceptions.
- Keep `MockSwiggyMcpClient` as the default local/test client.
- Add Meta Cloud WhatsApp sender payload/error tests for sandbox mode.

## Automated Verification

| Command | Result | Coverage |
|---|---|---|
| `cd src/backend && .venv/bin/python -m pytest tests/test_swiggy_mcp.py tests/test_whatsapp_sender.py tests/test_whatsapp_webhook.py tests/test_session_api.py` | Pass: 36 tests | Swiggy MCP normalization, error mapping, client mode selection, Meta sender payload/error mapping, webhook handoff, and session checkout regression. |
| `src/backend/.venv/bin/python -m ruff check src/backend/app src/backend/tests` | Pass | Backend lint check. |
| `make test` | Pass: 65 backend tests, 20 frontend tests | Full backend and frontend regression suite. |
| `make frontend-build` | Pass | Production frontend bundle. |

## Manual Verification To Run

Use [manual-ui-test-plan.md](../manual-ui-test-plan.md):

- `API-32`: verify Swiggy MCP response normalization from recorded or fake MCP
  responses.
- `API-33`: verify MCP tool errors map to application exceptions.
- `API-34`: verify mock mode stays default and MCP mode requires
  `SWIGGY_MCP_SERVER_PATH`.
- `API-35`: verify Meta WhatsApp sandbox sender payload shape.

Manual sandbox verification requires real provider credentials and an MCP server:

```bash
SWIGGY_CLIENT_MODE=mcp
SWIGGY_MCP_SERVER_PATH=/absolute/path/to/swiggy-mcp-server
SWIGGY_MCP_SERVER_ENV={"SWIGGY_ENV":"sandbox"}
WHATSAPP_PROVIDER_MODE=meta
WHATSAPP_ACCESS_TOKEN=<sandbox-token>
WHATSAPP_PHONE_NUMBER_ID=<sandbox-phone-number-id>
```

## Manual Verification Completed

Not run against live Swiggy MCP or Meta sandbox credentials. Automated tests cover
the integration boundaries without making network calls.

## Regressions

No regressions found in targeted integration tests, webhook/session regression
tests, the full verification suite, production frontend build, or backend lint.

## Known Limits

The Swiggy MCP stdio runner expects a configured command that accepts a JSON tool
request on stdin and returns JSON on stdout. Live sandbox behavior still depends
on the actual MCP server and provider credentials.
