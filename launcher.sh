#!/usr/bin/env bash
set -euo pipefail

: "${PROXY_PORT:=8501}"
MENTAL_PORT=8601
ADMIN_PORT=8602

timestamp() { date --utc +'%Y-%m-%dT%H:%M:%SZ'; }
log() { printf '[%s] %s\n' "$(timestamp)" "$*"; }

if [ -n "${GOOGLE_APPLICATION_CREDENTIALS_JSON:-}" ]; then
  log "Writing service account JSON to /tmp/sa.json"
  printf "%s" "$GOOGLE_APPLICATION_CREDENTIALS_JSON" > /tmp/sa.json
  export GOOGLE_APPLICATION_CREDENTIALS=/tmp/sa.json
else
  log "GOOGLE_APPLICATION_CREDENTIALS_JSON not set; Firestore may fallback to JSON or ambient creds"
fi

_start_bg() {
  eval "$1" > >(sed -u "s/^/[$(timestamp)] [child] /") 2> >(sed -u "s/^/[$(timestamp)] [child] /" >&2) &
  echo $!
}

MENTAL_PID=""
if [ -f ./mental.py ]; then
  log "Starting mental.py on port ${MENTAL_PORT}"
  MENTAL_CMD="streamlit run ./mental.py --server.port ${MENTAL_PORT} --server.address 0.0.0.0 --server.headless true"
  MENTAL_PID=$(_start_bg "$MENTAL_CMD")
  log "Started mental.py (PID ${MENTAL_PID}) -> http://127.0.0.1:${MENTAL_PORT}"
else
  log "mental.py not found; skipping"
fi

ADMIN_PID=""
if [ -f ./Admin.py ]; then
  log "Starting Admin.py on port ${ADMIN_PORT}"
  ADMIN_CMD="streamlit run ./Admin.py --server.port ${ADMIN_PORT} --server.address 0.0.0.0 --server.headless true"
  ADMIN_PID=$(_start_bg "$ADMIN_CMD")
  log "Started Admin.py (PID ${ADMIN_PID}) -> http://127.0.0.1:${ADMIN_PORT}"
else
  log "Admin.py not found; skipping"
fi

_term() {
  log "Termination signal received — killing children"
  if [ -n "${MENTAL_PID:-}" ]; then kill -TERM "$MENTAL_PID" 2>/dev/null || true; fi
  if [ -n "${ADMIN_PID:-}" ]; then kill -TERM "$ADMIN_PID" 2>/dev/null || true; fi
  sleep 2
  exit 0
}
trap _term SIGTERM SIGINT

_wait_for_port() {
  local p=$1; local tries=0; local max=20
  if command -v curl >/dev/null 2>&1; then
    until curl -sf "http://127.0.0.1:${p}" >/dev/null 2>&1 || [ $tries -ge $max ]; do
      tries=$((tries+1))
      log "Waiting for port ${p} (attempt ${tries}/${max})..."
      sleep 1
    done
    [ $tries -lt $max ] && log "Port ${p} is responding" || log "Timeout waiting for port ${p}"
  else
    log "curl missing; sleeping 2s"
    sleep 2
  fi
}

if [ -n "${MENTAL_PID:-}" ]; then _wait_for_port "${MENTAL_PORT}"; fi
if [ -n "${ADMIN_PID:-}" ]; then _wait_for_port "${ADMIN_PORT}"; fi

export MAIN_TARGET="http://127.0.0.1:${MENTAL_PORT}"
export ADMIN_TARGET="http://127.0.0.1:${ADMIN_PORT}"
export PORT="${PROXY_PORT}"

log "Launching proxy on ${PROXY_PORT} -> main:${MAIN_TARGET}, admin:${ADMIN_TARGET}"

exec python proxy.py
