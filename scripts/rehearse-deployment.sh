#!/usr/bin/env bash
# Rehearses EasyOrder's production topology (infra/docker-compose.production.yml)
# end to end on local Docker: runs the unit test suites, builds every image,
# deploys db -> migrate -> backend -> frontend/Caddy, verifies the static PWA
# serves and /api/* actually reaches the backend (not the SPA fallback),
# checks security headers, log rotation, and migration idempotency, rehearses
# a full simulated instance loss + recovery, then tears everything down.
#
# This is the scripted form of the "Verify it yourself" section in
# docs/runbooks/deployment.md — run it any time you want to re-confirm the
# topology actually works, not just read that it once did.
#
# Requires: Docker Desktop (or an equivalent Docker daemon) running.
# Requires NO real credentials — every integration rehearses in mock mode.
#
# Usage:
#   scripts/rehearse-deployment.sh                  # full rehearsal
#   scripts/rehearse-deployment.sh --skip-unit-tests # skip make test (faster)

set -euo pipefail
cd "$(dirname "$0")/.."

SKIP_UNIT_TESTS=0
for arg in "$@"; do
  case "$arg" in
    --skip-unit-tests) SKIP_UNIT_TESTS=1 ;;
    *) echo "Unknown argument: $arg" >&2; exit 1 ;;
  esac
done

PROJECT="${PROJECT:-easyorder-rehearsal}"
COMPOSE_FILE="infra/docker-compose.production.yml"
ENV_FILE="$(mktemp)"
POSTGRES_PASSWORD="rehearsal-$(date +%s 2>/dev/null || echo static)-$$"

pass() { printf '    \033[32mOK\033[0m %s\n' "$1"; }
step() { printf '\n==> %s\n' "$1"; }
fail() { printf '    \033[31mFAIL\033[0m %s\n' "$1" >&2; exit 1; }

find_free_port() {
  python3 - <<'PY'
import socket
s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.bind(("127.0.0.1", 0))
print(s.getsockname()[1])
s.close()
PY
}

FRONTEND_PORT="${FRONTEND_PORT:-$(find_free_port)}"

cleanup() {
  step "Cleaning up (containers, network, volumes, rehearsal images)"
  docker compose -f "$COMPOSE_FILE" --env-file "$ENV_FILE" -p "$PROJECT" down --volumes >/dev/null 2>&1 || true
  docker rmi "${PROJECT}-backend" "${PROJECT}-frontend" "${PROJECT}-migrate" >/dev/null 2>&1 || true
  rm -f "$ENV_FILE"
}
trap cleanup EXIT INT TERM

write_env() {
  cat > "$ENV_FILE" <<EOF
POSTGRES_PASSWORD=${POSTGRES_PASSWORD}
APP_ENV=production
PUBLIC_APP_BASE_URL=http://localhost:${FRONTEND_PORT}
WHATSAPP_PROVIDER_MODE=mock
WHATSAPP_VERIFY_TOKEN=rehearsal-verify-token
WHATSAPP_APP_SECRET=rehearsal-app-secret
FRONTEND_PORT=${FRONTEND_PORT}
EOF
}

compose() {
  docker compose -f "$COMPOSE_FILE" --env-file "$ENV_FILE" -p "$PROJECT" "$@"
}

wait_healthy() {
  attempt=0
  until curl --fail --silent "http://localhost:${FRONTEND_PORT}/" >/dev/null 2>&1; do
    attempt=$((attempt + 1))
    if [ "$attempt" -ge 60 ]; then
      echo "Timed out waiting for http://localhost:${FRONTEND_PORT}/" >&2
      compose logs --tail 60
      exit 1
    fi
    sleep 1
  done
}

if [ "$SKIP_UNIT_TESTS" -eq 0 ]; then
  step "Running unit test suites (make test) — skip with --skip-unit-tests"
  make test
  pass "backend + frontend unit tests"
else
  step "Skipping unit test suites (--skip-unit-tests)"
fi

step "Building images (db is a pulled base image; migrate, backend, frontend are built)"
write_env
compose build
pass "all images built"

step "Deploying db -> migrate -> backend -> frontend/Caddy (http://localhost:${FRONTEND_PORT})"
compose up -d
wait_healthy
pass "stack is up and the frontend responds"

step "Container health"
for name in db backend frontend; do
  status="$(docker inspect "${PROJECT}-${name}-1" --format '{{if .State.Health}}{{.State.Health.Status}}{{else}}(no healthcheck){{end}}' 2>/dev/null || echo missing)"
  case "$status" in
    healthy|"(no healthcheck)") pass "$name: $status" ;;
    *) fail "$name is not healthy (status: $status)" ;;
  esac
done

step "Migration ran and is idempotent"
migrate_log="$(compose logs migrate 2>&1)"
echo "$migrate_log" | grep -qiE "applied|already up to date" || fail "migrate log had no applied/up-to-date line:\n$migrate_log"
echo "$migrate_log" | grep -qi "error" && fail "migrate log contains an error:\n$migrate_log"
pass "migrate applied pending migrations (or confirmed up to date) cleanly"

step "Static PWA is served"
curl --fail --silent "http://localhost:${FRONTEND_PORT}/" | grep -q "EasyOrder" \
  || fail "homepage did not contain expected content"
pass "homepage serves the built PWA"

step "/api/* actually reaches the backend (not the SPA fallback)"
api_response="$(curl --silent "http://localhost:${FRONTEND_PORT}/api/session/rehearsal-check?token=x")"
echo "$api_response" | grep -q "Session not found" \
  || fail "expected a real backend JSON error, got: $api_response"
pass "proxy reaches backend: $api_response"

step "Security headers present on the homepage"
headers="$(curl --silent --dump-header - "http://localhost:${FRONTEND_PORT}/" --output /dev/null)"
for header in "x-frame-options" "x-content-type-options" "referrer-policy"; do
  echo "$headers" | grep -qi "^${header}:" || fail "missing header: $header"
done
pass "x-frame-options, x-content-type-options, referrer-policy all present"

step "Backend /healthz and /readyz (checked from inside the network — backend has no published host port)"
backend_healthz="$(compose exec -T backend python -c "import urllib.request; print(urllib.request.urlopen('http://127.0.0.1:8000/healthz').read().decode())")"
echo "$backend_healthz" | grep -q '"status":"ok"' || fail "healthz did not report ok: $backend_healthz"
backend_readyz="$(compose exec -T backend python -c "import urllib.request; print(urllib.request.urlopen('http://127.0.0.1:8000/readyz').read().decode())")"
echo "$backend_readyz" | grep -q '"status":"ready"' || fail "readyz did not report ready: $backend_readyz"
pass "healthz + readyz both report healthy"

step "Log rotation configured on every container"
for name in db backend frontend; do
  config="$(docker inspect "${PROJECT}-${name}-1" --format '{{json .HostConfig.LogConfig.Config}}')"
  echo "$config" | grep -q '"max-size":"10m"' && echo "$config" | grep -q '"max-file":"5"' \
    || fail "unexpected log config on $name: $config"
done
pass "10m x 5 files on db, backend, and frontend"

step "Rehearsing instance recovery: full teardown (containers, network, volumes), then rebuild from nothing but this repo's config"
compose down --volumes
compose up -d
wait_healthy
migrate_log_after_recovery="$(compose logs migrate 2>&1)"
echo "$migrate_log_after_recovery" | grep -qi "applied" || fail "recovery did not reapply migrations from a clean volume"
pass "recovered to healthy from a clean slate, migrations reapplied from scratch"

echo ""
echo "PASS — EasyOrder production topology rehearsed successfully."
