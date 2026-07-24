SHELL := /bin/bash

BACKEND_PYTHON := src/backend/.venv/bin/python
BACKEND_PORT ?= 8000
FRONTEND_PORT ?= 5173

.PHONY: setup up dev-down test check-ports backend-venv backend-install backend-dev backend-test backend-smoke frontend-install frontend-dev frontend-build frontend-test db-up db-migrate db-rollback db-down smoke demo-smoke security-smoke mock-mcp-install mock-mcp-up mock-mcp-test data-retention data-retention-dry-run db-migrate-versioned db-migrate-versioned-down prod-build prod-up prod-down

setup: backend-install frontend-install

check-ports:
	@if lsof -nP -iTCP:$(BACKEND_PORT) -sTCP:LISTEN >/dev/null 2>&1; then \
		echo "Port $(BACKEND_PORT) is already in use."; \
		lsof -nP -iTCP:$(BACKEND_PORT) -sTCP:LISTEN; \
		echo "Run 'make dev-down' to stop the local EasyOrder dev servers, or run with BACKEND_PORT=<free-port>."; \
		exit 1; \
	fi
	@if lsof -nP -iTCP:$(FRONTEND_PORT) -sTCP:LISTEN >/dev/null 2>&1; then \
		echo "Port $(FRONTEND_PORT) is already in use."; \
		lsof -nP -iTCP:$(FRONTEND_PORT) -sTCP:LISTEN; \
		echo "Run 'make dev-down' to stop the local EasyOrder dev servers, or run with FRONTEND_PORT=<free-port>."; \
		exit 1; \
	fi

dev-down:
	@pids="$$(lsof -tiTCP:$(BACKEND_PORT) -sTCP:LISTEN 2>/dev/null || true)"; \
	if [ -n "$$pids" ]; then \
		echo "Stopping backend process(es) on port $(BACKEND_PORT): $$pids"; \
		kill $$pids; \
	fi
	@pids="$$(lsof -tiTCP:$(FRONTEND_PORT) -sTCP:LISTEN 2>/dev/null || true)"; \
	if [ -n "$$pids" ]; then \
		echo "Stopping frontend process(es) on port $(FRONTEND_PORT): $$pids"; \
		kill $$pids; \
	fi
	@$(MAKE) db-down

up:
	set -euo pipefail; \
	db_started="0"; \
	backend_pid=""; \
	frontend_pid=""; \
	cleanup() { \
		status=$$?; \
		trap - EXIT INT TERM; \
		if [ -n "$$backend_pid" ]; then kill "$$backend_pid" 2>/dev/null || true; fi; \
		if [ -n "$$frontend_pid" ]; then kill "$$frontend_pid" 2>/dev/null || true; fi; \
		wait 2>/dev/null || true; \
		if [ "$$db_started" = "1" ]; then $(MAKE) db-down; fi; \
		exit $$status; \
	}; \
	trap cleanup EXIT INT TERM; \
	$(MAKE) setup; \
	$(MAKE) check-ports; \
	$(MAKE) db-up; \
	db_started="1"; \
	$(MAKE) db-migrate; \
	$(MAKE) backend-test; \
	$(MAKE) frontend-test; \
	$(MAKE) frontend-build; \
	$(MAKE) backend-dev & backend_pid=$$!; \
	$(MAKE) frontend-dev & frontend_pid=$$!; \
	wait

test: backend-test frontend-test

backend-venv:
	cd src/backend && python3 -m venv .venv

backend-install: backend-venv
	cd src/backend && .venv/bin/python -m pip install -r requirements.txt -r requirements-dev.txt

backend-dev:
	cd src/backend && .venv/bin/python -m uvicorn app.main:app --reload --port $(BACKEND_PORT)

backend-test:
	cd src/backend && APP_ENV=local PERSISTENCE_MODE=memory PUBLIC_APP_BASE_URL=http://localhost:5173 WHATSAPP_PROVIDER_MODE=mock WHATSAPP_VERIFY_TOKEN=local-verify-token WHATSAPP_APP_SECRET= SWIGGY_CLIENT_MODE=mock LLM_MODE=mock .venv/bin/python -m pytest

backend-smoke:
	cd src/backend && python3 -m compileall app tests

frontend-install:
	cd src/frontend && npm install

frontend-dev:
	cd src/frontend && npm run dev -- --port $(FRONTEND_PORT) --strictPort

frontend-build:
	cd src/frontend && npm run build

frontend-test:
	cd src/frontend && npm run test

db-up:
	docker compose -f infra/docker-compose.yml up -d db

db-migrate:
	@for migration in infra/migrations/0*.sql; do \
		case "$$migration" in *.down.sql) continue ;; esac; \
		echo "applying $$migration"; \
		docker compose -f infra/docker-compose.yml exec -T db psql -U easyorder -d easyorder -v ON_ERROR_STOP=1 -f - < "$$migration" || exit 1; \
	done

db-rollback:
	@for migration in $$(ls -r infra/migrations/0*.down.sql); do \
		echo "applying $$migration"; \
		docker compose -f infra/docker-compose.yml exec -T db psql -U easyorder -d easyorder -v ON_ERROR_STOP=1 -f - < "$$migration" || exit 1; \
	done

# Versioned alternative to db-migrate/db-rollback: tracks applied migrations
# in a schema_migrations table instead of blindly reapplying every *.sql file
# every time. Connects directly via DATABASE_URL (no docker exec needed), so
# this is what a real deploy (or CI) should run, not just local dev.
db-migrate-versioned:
	$(BACKEND_PYTHON) scripts/run_migrations.py --database-url $${DATABASE_URL:-postgresql://easyorder:easyorder@localhost:5432/easyorder}

db-migrate-versioned-down:
	$(BACKEND_PYTHON) scripts/run_migrations.py --down --database-url $${DATABASE_URL:-postgresql://easyorder:easyorder@localhost:5432/easyorder}

db-down:
	docker compose -f infra/docker-compose.yml down

smoke: backend-smoke frontend-build

demo-smoke:
	APP_ENV=local PERSISTENCE_MODE=memory PUBLIC_APP_BASE_URL=http://localhost:5173 WHATSAPP_PROVIDER_MODE=mock WHATSAPP_VERIFY_TOKEN=local-verify-token WHATSAPP_APP_SECRET= SWIGGY_CLIENT_MODE=mock LLM_MODE=mock $(BACKEND_PYTHON) scripts/easyorder_demo_smoke.py

security-smoke:
	APP_ENV=local PERSISTENCE_MODE=memory PUBLIC_APP_BASE_URL=http://localhost:5173 WHATSAPP_PROVIDER_MODE=mock WHATSAPP_VERIFY_TOKEN=local-verify-token WHATSAPP_APP_SECRET= SWIGGY_CLIENT_MODE=mock LLM_MODE=mock $(BACKEND_PYTHON) scripts/easyorder_security_smoke.py

mock-mcp-install:
	cd services/mock-swiggy-mcp && python3 -m venv .venv && .venv/bin/pip install -r requirements.txt -r requirements-dev.txt

mock-mcp-up:
	cd services/mock-swiggy-mcp && MOCK_MCP_AUTH_TOKEN=$${MOCK_MCP_AUTH_TOKEN:-dev-token} .venv/bin/python app/server.py

mock-mcp-test:
	cd services/mock-swiggy-mcp && .venv/bin/python -m pytest

data-retention:
	$(BACKEND_PYTHON) scripts/easyorder_data_retention.py --retention-days $${RETENTION_DAYS:-90}

data-retention-dry-run:
	$(BACKEND_PYTHON) scripts/easyorder_data_retention.py --retention-days $${RETENTION_DAYS:-90} --dry-run

# Production topology rehearsal/deploy: db -> migrate -> backend + frontend/Caddy.
# Requires PROD_ENV_FILE pointing at a real env file (see docs/runbooks/deployment.md);
# never commit that file. PROJECT lets multiple rehearsals coexist without colliding.
PROD_ENV_FILE ?= infra/.env.production
PROJECT ?= easyorder-prod

prod-build:
	docker compose -f infra/docker-compose.production.yml --env-file $(PROD_ENV_FILE) -p $(PROJECT) build

prod-up:
	docker compose -f infra/docker-compose.production.yml --env-file $(PROD_ENV_FILE) -p $(PROJECT) up -d

prod-down:
	docker compose -f infra/docker-compose.production.yml --env-file $(PROD_ENV_FILE) -p $(PROJECT) down
