# Architecture diagrams

The three PNGs in this directory are **generated**, not drawn. Their source is the HTML in
`src/`, so a change to the architecture and a change to the diagram can land in the same
commit. The previous PNGs had no source at all, which is how they came to show Cloud
Firestore, Firebase Anonymous Auth, stdio JSON-RPC and a Budget Worker long after none of
those were true.

| PNG | Source | Shows |
| --- | --- | --- |
| `01-high-level-architecture.png` | `src/01-high-level-architecture.html` | WhatsApp → FastAPI → Swiggy MCP, PostgreSQL persistence, the request flow end to end |
| `02-fastapi-application-architecture.png` | `src/02-fastapi-application-architecture.html` | Routers, services, the host/guest/web token systems, and the adapter seams |
| `03-agentic-framework-architecture.png` | `src/03-agentic-framework-architecture.html` | The LangGraph node chain, outcomes, and the stack as it actually ships |

## Regenerating

Headless Chrome renders the page at a fixed window size; the CSS uses `height: 100vh`, so
the window size *is* the canvas. Heights differ per diagram because content differs.

```bash
cd docs/diagrams/src
CHROME="/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"

"$CHROME" --headless --disable-gpu --hide-scrollbars \
  --window-size=1024,820 --screenshot=../01-high-level-architecture.png \
  01-high-level-architecture.html

"$CHROME" --headless --disable-gpu --hide-scrollbars \
  --window-size=1024,860 --screenshot=../02-fastapi-application-architecture.png \
  02-fastapi-application-architecture.html

"$CHROME" --headless --disable-gpu --hide-scrollbars \
  --window-size=1024,908 --screenshot=../03-agentic-framework-architecture.png \
  03-agentic-framework-architecture.html
```

If you add content and it clips, raise that diagram's window height and update it here.
Open the HTML in a normal browser while editing — it renders identically.

## Editing

`src/_style.css` holds the shared visual language: panel colours (`p-client`, `p-server`,
`p-external`, `p-store`, `p-auth`, `p-neutral`), the `box` component, coloured left borders
(`tint-food`, `tint-llm`, `tint-guard`, `tint-store`, `tint-profile`), the numbered `flow`
strip and the dashed `note` footer.

Each diagram ends with a `note` stating what it deliberately does **not** claim. Keep that
habit: the footnotes are where the old diagrams' drift would have been caught.

## Keeping them true

These are the frames a judge pauses on, so every box should be defensible from a file:

- Persistence is PostgreSQL via `asyncpg` — ADR 0001 supersedes the original Firestore
  decision, and ADR 0007 dropped row-level security in favour of app-layer authorization.
- The Swiggy MCP client speaks **Streamable HTTP** (`services/swiggy_mcp.py`), not stdio.
- The graph fans out **two** concurrent workers; budget and portion arithmetic lives in the
  output-guardrail node (`services/agent.py`).
- `profile_defaults` sits between the intent parser and the workers
  (`services/profile_builder.py`).
- Cart sync is client polling every 2.5s (`useSupabaseCartRealtime.ts`), not a realtime
  subscription — the name predates the implementation.
