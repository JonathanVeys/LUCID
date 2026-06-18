#!/usr/bin/env bash
#
# LUCID — one-shot dev launcher
# ------------------------------------------------------------------
# Boots the Postgres DB (Docker), the FastAPI backend, and the React
# frontend. Ctrl+C stops the backend + frontend cleanly. The DB is
# left running so seed data survives between runs.
#
#   ./run.sh             boot everything
#   ./run.sh --reseed    wipe + reseed the DB first, then boot
#
# Place this file at the REPO ROOT (next to your compose file, backend/
# and frontend/). Make it executable once:  chmod +x run.sh
# ------------------------------------------------------------------
set -euo pipefail

# ===== CONFIG — confirm these match your project ==================
BACKEND_DIR="backend"
FRONTEND_DIR="frontend"
APP_MODULE="backend.main:app"        # uvicorn target: <file>:<FastAPI instance>
BACKEND_HOST="127.0.0.1"
BACKEND_PORT="8000"
DB_PORT="5432"               # host port Postgres is published on
FRONTEND_NPM_SCRIPT="dev"    # "dev" for Vite, "start" for Create React App
ENV_FILE="${BACKEND_DIR}/.env"   # holds your model API key etc.
# =================================================================

# Resolve the repo root from the script's own location. Computing it this
# way (rather than $PWD) also sidesteps the trailing-space-in-folder-name
# issue, since every path below is built from and quoted against this.
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

RESEED=0
[ "${1:-}" = "--reseed" ] && RESEED=1

log()  { printf '\n\033[1;36m==>\033[0m %s\n' "$1"; }
warn() { printf '\n\033[1;33m[!]\033[0m %s\n' "$1"; }
die()  { printf '\n\033[1;31m[x]\033[0m %s\n' "$1" >&2; exit 1; }

# ----- prerequisites ---------------------------------------------
command -v docker  >/dev/null 2>&1 || die "docker not found — install Docker."
command -v node    >/dev/null 2>&1 || die "node not found — install Node.js."
command -v npm     >/dev/null 2>&1 || die "npm not found — install Node.js."
command -v python3 >/dev/null 2>&1 || die "python3 not found — install Python 3."

# docker compose v2 ("docker compose") vs v1 ("docker-compose")
if docker compose version >/dev/null 2>&1; then
  DC="docker compose"
elif command -v docker-compose >/dev/null 2>&1; then
  DC="docker-compose"
else
  die "Neither 'docker compose' nor 'docker-compose' is available."
fi

[ -f "$ENV_FILE" ] || warn "No ${ENV_FILE} found. The dashboard pipeline calls a \
model and will fail without credentials. Create it before demoing."

# ----- 1. database ------------------------------------------------
if [ "$RESEED" -eq 1 ]; then
  log "Reseeding: tearing down DB and volumes (docker compose down -v)"
  $DC down -v
fi

log "Starting Postgres (docker compose up -d)"
$DC up -d

# Wait until Postgres actually accepts connections, not just until the
# container exists. Backend startup opens DB connections immediately, so
# starting it too early is the classic boot-order crash.
log "Waiting for Postgres on ${BACKEND_HOST}:${DB_PORT} ..."
ready=0
for _ in $(seq 1 60); do
  if command -v pg_isready >/dev/null 2>&1; then
    pg_isready -h "$BACKEND_HOST" -p "$DB_PORT" >/dev/null 2>&1 && { ready=1; break; }
  else
    # No psql client on host: fall back to a raw TCP check.
    (exec 3<>"/dev/tcp/${BACKEND_HOST}/${DB_PORT}") 2>/dev/null && \
      { exec 3>&- 3<&-; ready=1; break; }
  fi
  sleep 1
done
[ "$ready" -eq 1 ] || die "Postgres did not become ready in time. Check '$DC logs'."
log "Postgres is ready."

# ----- 2. backend -------------------------------------------------
log "Setting up backend (${BACKEND_DIR})"
pushd "$BACKEND_DIR" >/dev/null

if [ ! -d .venv ]; then
  log "Creating virtualenv (backend/.venv)"
  python3 -m venv .venv
fi
# shellcheck disable=SC1091
source .venv/bin/activate
python -m pip install -q --upgrade pip
if [ -f requirements.txt ]; then
  log "Installing backend dependencies"
  pip install -q -r requirements.txt
else
  warn "No backend/requirements.txt found — skipping dependency install."
fi

# Run uvicorn FROM INSIDE backend/ so imports resolve (no 'backend.' prefix).
log "Launching FastAPI on http://${BACKEND_HOST}:${BACKEND_PORT}"
uvicorn "$APP_MODULE" --host "$BACKEND_HOST" --port "$BACKEND_PORT" --reload &
BACKEND_PID=$!
popd >/dev/null

# ----- 3. frontend ------------------------------------------------
log "Setting up frontend (${FRONTEND_DIR})"
pushd "$FRONTEND_DIR" >/dev/null
if [ ! -d node_modules ]; then
  log "Installing frontend dependencies (npm install)"
  npm install
fi
log "Launching React dev server (npm run ${FRONTEND_NPM_SCRIPT})"
npm run "$FRONTEND_NPM_SCRIPT" &
FRONTEND_PID=$!
popd >/dev/null

# ----- cleanup on exit -------------------------------------------
cleanup() {
  log "Shutting down backend + frontend"
  [ -n "${FRONTEND_PID:-}" ] && kill "$FRONTEND_PID" 2>/dev/null || true
  [ -n "${BACKEND_PID:-}" ]  && kill "$BACKEND_PID"  2>/dev/null || true
  # kill any stragglers spawned by npm/uvicorn under our PIDs
  [ -n "${FRONTEND_PID:-}" ] && pkill -P "$FRONTEND_PID" 2>/dev/null || true
  [ -n "${BACKEND_PID:-}" ]  && pkill -P "$BACKEND_PID"  2>/dev/null || true
  echo
  echo "Backend + frontend stopped. The database is still running."
  echo "Stop it with:  $DC down        (add -v to also wipe seed data)"
}
trap cleanup INT TERM EXIT

cat <<EOF

------------------------------------------------------------------
  LUCID is up.
    Frontend : http://localhost:5173      (Vite default; check terminal)
    Backend  : http://${BACKEND_HOST}:${BACKEND_PORT}
    API docs : http://${BACKEND_HOST}:${BACKEND_PORT}/docs
  Press Ctrl+C to stop the backend and frontend.
------------------------------------------------------------------
EOF

# Stay attached so the logs stream and Ctrl+C triggers cleanup.
wait