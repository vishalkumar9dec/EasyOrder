# Architecture diagrams

The three PNGs in this directory are **generated**, not drawn. Their source is hand-written
SVG (inside a thin HTML wrapper) in `src/`, so a change to the architecture and a change to
the diagram can land in the same commit. The previous PNGs had no source at all, which is
how they came to show Cloud Firestore, Firebase Anonymous Auth, stdio JSON-RPC and a Budget
Worker long after none of those were true.

They are node-and-edge diagrams: every component is a box, and every connection is a drawn,
labelled arrow you can follow with a finger. Numbered badges mark the order of a request.

| PNG | Source | Shows |
| --- | --- | --- |
| `01-high-level-architecture.png` | `src/01-high-level-architecture.html` | WhatsApp → FastAPI → Swiggy MCP, PostgreSQL persistence, the request flow end to end |
| `02-fastapi-application-architecture.png` | `src/02-fastapi-application-architecture.html` | Routers, services, the host/guest/web token systems, and the adapter seams |
| `03-agentic-framework-architecture.png` | `src/03-agentic-framework-architecture.html` | The LangGraph node chain, outcomes, and the stack as it actually ships |

## Regenerating

Headless Chrome renders each page at the SVG's own size. The window size must match the
`width`/`height` on the `<svg>` element, which differs per diagram.

```bash
cd docs/diagrams/src
CHROME="/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"

"$CHROME" --headless --disable-gpu --hide-scrollbars \
  --window-size=1120,860 --screenshot=../01-high-level-architecture.png \
  01-high-level-architecture.html

"$CHROME" --headless --disable-gpu --hide-scrollbars \
  --window-size=1120,900 --screenshot=../02-fastapi-application-architecture.png \
  02-fastapi-application-architecture.html

"$CHROME" --headless --disable-gpu --hide-scrollbars \
  --window-size=1120,960 --screenshot=../03-agentic-framework-architecture.png \
  03-agentic-framework-architecture.html
```

If you add content and it clips, raise both the `<svg>` height and the window height here.
Open the HTML in a normal browser while editing — it renders identically, and SVG
coordinates make it easy to nudge a box or reroute an arrow.

## Editing

`src/_diagram.css` holds the shared visual language: panel fills (`p-client`, `p-server`,
`p-external`, `p-store`, `p-auth`, `p-neutral`), the `node` box with coloured strokes
(`a-food`, `a-llm`, `a-guard`, `a-store`, `a-profile`), the edge styles (`edge`,
`edge-both` for two-way, `edge-dashed` for optional or out-of-band), numbered `badge`
circles, and the dashed `note-box` footer.

Boxes are `<rect>` plus `<text>` at explicit coordinates; connections are `<path>` with
elbow routing (`M x y H x V y H x`). Keep arrows out of boxes they do not connect — a line
crossing a component reads as a connection to it.

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
