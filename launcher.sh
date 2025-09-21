#!/usr/bin/env bash
set -euo pipefail

# Run proxy on Railway-exposed port 8501 (keep as before)
: "${PROXY_PORT:=8501}"
MENTAL_PORT=8601
ADMIN_PORT=8602

timestamp() { date --utc +'%Y-%m-%dT%H:%M:%SZ'; }
log() { printf '[%s] %s\n' "$(timestamp)" "$*"; }

# write service account JSON if provided
if [ -n "${GOOGLE_APPLICATION_CREDENTIALS_JSON:-}" ]; then
  log "Writing service account JSON to /tmp/sa.json"
  printf "%s" "$GOOGLE_APPLICATION_CREDENTIALS_JSON" > /tmp/sa.json
  export GOOGLE_APPLICATION_CREDENTIALS=/tmp/sa.json
fi

# helper to start with nohup and redirect output to a logfile
_start_nohup() {
  local cmd="$1"
  local logfile="$2"
  # launch under nohup so it won't get killed by starter, redirect stdout/stderr
  nohup bash -lc "$cmd" > "$logfile" 2>&1 &
  echo $!
}

# start mental, capture output
MENTAL_PID=""
if [ -f ./mental.py ]; then
  log "Launching mental.py -> port ${MENTAL_PORT}, logging to /tmp/mental.log"
  MENTAL_CMD="streamlit run ./mental.py --server.port ${MENTAL_PORT} --server.address 0.0.0.0 --server.headless true"
  MENTAL_PID=$(_start_nohup "$MENTAL_CMD" "/tmp/mental.log")
  log "mental PID=${MENTAL_PID}"
  # tail the logfile to container stdout so logs appear in Railway
  ( tail -n +1 -F /tmp/mental.log ) > /proc/1/fd/1 2>/proc/1/fd/2 &
else
  log "mental.py not found; skipping"
fi

# start Admin, capture output
ADMIN_PID=""
if [ -f ./Admin.py ]; then
  log "Launching Admin.py -> port ${ADMIN_PORT}, logging to /tmp/admin.log"
  ADMIN_CMD="streamlit run ./Admin.py --server.port ${ADMIN_PORT} --server.address 0.0.0.0 --server.headless true"
  ADMIN_PID=$(_start_nohup "$ADMIN_CMD" "/tmp/admin.log")
  log "admin PID=${ADMIN_PID}"
  # tail the logfile to container stdout so logs appear in Railway
  ( tail -n +1 -F /tmp/admin.log ) > /proc/1/fd/1 2>/proc/1/fd/2 &
else
  log "Admin.py not found; skipping"
fi

# graceful shutdown
_term() {
  log "Termination signal received — killing children (mental=${MENTAL_PID:-none}, admin=${ADMIN_PID:-none})"
  if [ -n "${MENTAL_PID:-}" ]; then kill -TERM "$MENTAL_PID" 2>/dev/null || true; fi
  if [ -n "${ADMIN_PID:-}" ]; then kill -TERM "$ADMIN_PID" 2>/dev/null || true; fi
  sleep 2
  exit 0
}
trap _term SIGTERM SIGINT

# wait for a port to respond
_wait_for_port() {
  local port=$1; local tries=0; local max=20
  if command -v curl >/dev/null 2>&1; then
    until curl -sf "http://127.0.0.1:${port}" >/dev/null 2>&1 || [ $tries -ge $max ]; do
      tries=$((tries+1))
      log "Waiting on port ${port} (attempt ${tries}/${max})..."
      sleep 1
    done
    if [ $tries -ge $max ]; then
      log "Timeout waiting for port ${port}"
      return 1
    fi
    log "Port ${port} responding"
    return 0
  else
    log "curl not available, sleeping 3s"
    sleep 3
    return 0
  fi
}

# probe mental and admin
if [ -n "${MENTAL_PID:-}" ]; then _wait_for_port "${MENTAL_PORT}" || log "mental did not respond in time"; fi
if [ -n "${ADMIN_PID:-}" ]; then _wait_for_port "${ADMIN_PORT}" || log "admin did not respond in time"; fi

# export for proxy
export MAIN_TARGET="http://127.0.0.1:${MENTAL_PORT}"
export ADMIN_TARGET="http://127.0.0.1:${ADMIN_PORT}"
export PORT="${PROXY_PORT}"

log "Starting proxy on ${PROXY_PORT} -> main:${MAIN_TARGET}, admin:${ADMIN_TARGET}"

# exec proxy (becomes PID 1)
exec python proxy.py
