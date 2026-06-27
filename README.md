# EasyOrder

EasyOrder is a WhatsApp-first group ordering system for coordinating Swiggy Food and
Instamart carts. The MVP starts as a mobile-first web app opened from a WhatsApp link,
with mock integrations by default so the product flow can be tested locally before live
WhatsApp, Swiggy, OAuth, or Supabase credentials are required.

## Project Structure

```text
.
├── docs/                    # Product, architecture, ADRs, and implementation plans
├── infra/                   # Local infrastructure such as PostgreSQL
├── src/
│   ├── backend/             # FastAPI service
│   └── frontend/            # React/Vite web app
├── Makefile                 # Common local commands
└── README.md
```

## Requirements

- Python 3.12+
- Node.js 22+
- Docker, for local PostgreSQL

## Backend Setup

```bash
make setup
cp src/backend/.env.example src/backend/.env
make backend-dev
```

Health checks:

```bash
curl http://localhost:8000/healthz
curl http://localhost:8000/readyz
```

Run backend tests:

```bash
make backend-test
```

## Frontend Setup

```bash
make setup
cp src/frontend/.env.example src/frontend/.env
make frontend-dev
```

Open the web app at [http://localhost:5173](http://localhost:5173).

The local app starts as a pre-session playground. It uses deterministic mock data only:
no LLM, WhatsApp, Swiggy, OAuth, Supabase, sessions, tokens, or RLS calls are made.

Build the frontend:

```bash
make frontend-build
```

## Local Database

Start PostgreSQL:

```bash
make db-up
```

Verify the database:

```bash
docker compose -f infra/docker-compose.yml exec db psql -U easyorder -d easyorder -c "SELECT 1;"
```

Stop PostgreSQL:

```bash
make db-down
```

Supabase local stack support can be added in later slices when Auth and Realtime are
needed. For now, PostgreSQL is the local persistence base and all external integrations
default to mock mode.

## Manual Verification

From a clean checkout, run setup once:

```bash
make setup
cp src/backend/.env.example src/backend/.env
cp src/frontend/.env.example src/frontend/.env
```

Start the services in separate terminals:

```bash
make db-up
make backend-dev
make frontend-dev
```

Verify the running services:

```bash
curl http://localhost:8000/healthz
curl http://localhost:8000/readyz
docker compose -f infra/docker-compose.yml exec db psql -U easyorder -d easyorder -c "SELECT 1;"
```

Open the web app at [http://localhost:5173](http://localhost:5173). The app should
render the local playground.

Review these mock use cases from the selector:

- Normal group order
- Over-budget cart
- Dietary mismatch
- Degraded Food availability
- Degraded Instamart availability
- Stock change at validation
- Price change at validation

For each use case, test the host-style prompt, editable cart quantities, budget and
dietary warnings, degraded-state messaging, host/guest toggle, and mock checkout
validation state.

Stop the long-running services when you are done:

```bash
make db-down
```

Use `Ctrl+C` in the backend and frontend terminals.

## Common Commands

```bash
make setup
make backend-smoke
make backend-test
make frontend-test
make frontend-build
make test
make smoke
```

## Troubleshooting

If port `8000` is already in use, stop the old backend process or run the backend on a
different port:

```bash
make backend-dev BACKEND_PORT=8001
```

If port `5173` is already in use, stop the old frontend process or run the web app on a
different port:

```bash
make frontend-dev FRONTEND_PORT=5174
```

## Environment

Environment samples live at:

- `src/backend/.env.example`
- `src/frontend/.env.example`

Do not commit real secrets. Mock mode is the expected local default for WhatsApp, Swiggy,
and LLM behavior.

## Documentation

- Product scope: `docs/easyorder-prd.md`
- High-level design: `docs/hld.md`
- Low-level design: `docs/lld.md`
- Delivery plan: `docs/implementation-plan.md`
- Task list: `docs/implementation-tasks.md`
- Domain glossary: `CONTEXT.md`
