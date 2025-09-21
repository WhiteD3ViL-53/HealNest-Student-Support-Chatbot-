#!/usr/bin/env bash
set -euo pipefail

: "${PORT:=8080}"
MENTAL_PORT=8501
ADMIN_PORT=8502

timestamp() {
  date --utc +'%Y-%m-%dT%H:%M:%SZ'
}

log() {
  printf '[%s] %s\n' "$(timestamp)" "$*"
}

# Write service account JSON if provided (safe)
if [ -n "${GOOGLE_APPLICATION_CREDENTIALS_JSON:-}" ]; then
  log "Writing service account JSON to /tmp/sa.json"
  # use printf to avoid extra newline issues
  printf "%s" "$GOOGLE_APPLICATION_CREDENTIALS_JSON" > /tmp/sa.json
  export GOOGLE_APPLICATION_CREDENTIALS=/tmp/sa.json
else
  log "GOOGLE_APPLICATION_CREDENTIALS_JSON not set; Firestore may fallback to JSON file or ambient creds"
fi

# Load .env for local debugging (no-op in production if .env absent)
if [ -f .env ]; then
  log "Loading .env"
  set -o allexport
  # shellcheck disable=SC1091
  source .env
  set +o allexport
fi

# helper: start background command and stream its stdout/stderr into container logs
_start_bg() {
  # $1 = command string
  eval "$1" > >(sed -u "s/^/[$(timestamp)] [child] /") 2> >(sed -u "s/^/[$(timestamp)] [child] /" >&2) &
  echo $!
}

# Start mental
MENTAL_PID=""
if [ -f ./mental.py ]; then
  log "Starting mental.py on port ${MENTAL_PORT}"
  MENTAL_CMD="streamlit run ./mental.py --server.port ${MENTAL_PORT} --server.address 0.0.0.0 --server.headless true"
  MENTAL_PID=$(_start_bg "$MENTAL_CMD")
  log "Started mental.py (PID ${MENTAL_PID}) -> http://127.0.0.1:${MENTAL_PORT}"
else
  log "mental.py not found; skipping mental service"
fi

# Start Admin
ADMIN_PID=""
if [ -f ./Admin.py ]; then
  log "Starting Admin.py on port ${ADMIN_PORT}"
  ADMIN_CMD="streamlit run ./Admin.py --server.port ${ADMIN_PORT} --server.address 0.0.0.0 --server.headless true"
  ADMIN_PID=$(_start_bg "$ADMIN_CMD")
  log "Started Admin.py (PID ${ADMIN_PID}) -> http://127.0.0.1:${ADMIN_PORT}"
else
  log "Admin.py not found; skipping admin service"
fi

# graceful shutdown forwarding
_term() {
  log "Termination signal received — forwarding to children"
  if [ -n "${MENTAL_PID:-}" ]; then
    kill -TERM "$MENTAL_PID" 2>/dev/null || true
  fi
  if [ -n "${ADMIN_PID:-}" ]; then
    kill -TERM "$ADMIN_PID" 2>/dev/null || true
  fi
  sleep 2
  exit 0
}
trap _term SIGTERM SIGINT

# wait helper (checks local http)
_wait_for_port() {
  local port=$1
  local tries=0
  local max=20
  if command -v curl >/dev/null 2>&1; then
    until curl -sf "http://127.0.0.1:${port}" >/dev/null 2>&1 || [ $tries -ge $max ]; do
      tries=$((tries+1))
      log "Waiting for service on port ${port} (attempt ${tries}/${max})..."
      sleep 1
    done
    if [ $tries -ge $max ]; then
      log "Timeout waiting for port ${port}"
      return 1
    fi
    log "Port ${port} is responding"
    return 0
  else
    # fallback sleep
    log "curl not available — sleeping 3s for port ${port}"
    sleep 3
    return 0
  fi
}

# Probe services
if [ -n "${MENTAL_PID:-}" ]; then
  _wait_for_port "${MENTAL_PORT}" || log "Warning: mental did not respond in time"
fi
if [ -n "${ADMIN_PID:-}" ]; then
  _wait_for_port "${ADMIN_PORT}" || log "Warning: admin did not respond in time"
fi

# Export proxy targets
export MAIN_TARGET="http://127.0.0.1:${MENTAL_PORT}"
export ADMIN_TARGET="http://127.0.0.1:${ADMIN_PORT}"
export PORT="${PORT}"

log "All child processes launched (mental PID=${MENTAL_PID:-none}, admin PID=${ADMIN_PID:-none})."
log "Starting proxy on port ${PORT} -> main:${MAIN_TARGET}, admin:${ADMIN_TARGET}"

# exec proxy makes it PID 1 so container stops when proxy exits and receives signals correctly
exec python proxy.py
