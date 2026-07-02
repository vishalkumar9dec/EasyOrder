SHELL := /bin/bash

BACKEND_PYTHON := src/backend/.venv/bin/python
BACKEND_PORT ?= 8000
FRONTEND_PORT ?= 5173

.PHONY: setup up test backend-venv backend-install backend-dev backend-test backend-smoke frontend-install frontend-dev frontend-build frontend-test db-up db-migrate db-rollback db-down smoke demo-smoke security-smoke

setup: backend-install frontend-install

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
	cd src/backend && .venv/bin/python -m pytest

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
	docker compose -f infra/docker-compose.yml exec -T db psql -U easyorder -d easyorder -v ON_ERROR_STOP=1 -f - < infra/migrations/0001_session_persistence.sql

db-rollback:
	docker compose -f infra/docker-compose.yml exec -T db psql -U easyorder -d easyorder -v ON_ERROR_STOP=1 -f - < infra/migrations/0001_session_persistence.down.sql

db-down:
	docker compose -f infra/docker-compose.yml down

smoke: backend-smoke frontend-build

demo-smoke:
	$(BACKEND_PYTHON) scripts/easyorder_demo_smoke.py

security-smoke:
	$(BACKEND_PYTHON) scripts/easyorder_security_smoke.py
