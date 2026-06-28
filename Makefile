BACKEND_PYTHON := src/backend/.venv/bin/python
BACKEND_PORT ?= 8000
FRONTEND_PORT ?= 5173

.PHONY: setup test backend-venv backend-install backend-dev backend-test backend-smoke frontend-install frontend-dev frontend-build frontend-test db-up db-migrate db-rollback db-down smoke

setup: backend-install frontend-install

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
