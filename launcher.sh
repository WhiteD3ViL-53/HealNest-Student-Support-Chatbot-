#!/usr/bin/env bash
set -euo pipefail

: "${PORT:=8080}"
MENTAL_PORT=8501
ADMIN_PORT=8502

_echo() {
  printf '[%s] %s\n' "$(date --utc +'%Y-%m-%dT%H:%M:%SZ')" "$*"
}

# If a service account JSON is provided via env, write it to /tmp/sa.json and export
if [ -n "${GOOGLE_APPLICATION_CREDENTIALS_JSON:-}" ]; then
  _echo "Writing service account JSON to /tmp/sa.json"
  # Use printf to avoid extra newlines
  printf "%s" "$GOOGLE_APPLICATION_CREDENTIALS_JSON" > /tmp/sa.json
  export GOOGLE_APPLICATION_CREDENTIALS=/tmp/sa.json
else
  _echo "GOOGLE_APPLICATION_CREDENTIALS_JSON not set; Firestore will rely on ambient credentials (if any)"
fi

# Load .env if present (local only)
if [ -f .env ]; then
  _echo "Loading .env"
  # export all non-comment lines
  set -o allexport
  # shellcheck disable=SC1091
  source .env
  set +o allexport
fi

# start a background process and capture PID helper
_start_bg() {
  local cmd=$1
  eval "$cmd" > >(cat -) 2> >(cat - >&2) &
  echo $!
}

# Start mental app
if [ -f ./mental.py ]; then
  _echo "Starting mental.py on port ${MENTAL_PORT}"
  MENTAL_CMD="streamlit run ./mental.py --server.port ${MENTAL_PORT} --server.address 0.0.0.0 --server.headless true"
  MENTAL_PID=$(_start_bg "$MENTAL_CMD")
else
  _echo "mental.py not found; skipping mental service"
  MENTAL_PID=""
fi

# Start Admin app (capital A; keep exact filename)
if [ -f ./Admin.py ]; then
  _echo "Starting Admin.py on port ${ADMIN_PORT}"
  ADMIN_CMD="streamlit run ./Admin.py --server.port ${ADMIN_PORT} --server.address 0.0.0.0 --server.headless true"
  ADMIN_PID=$(_start_bg "$ADMIN_CMD")
else
  _echo "Admin.py not found; skipping admin service"
  ADMIN_PID=""
fi

# Forward signals to children for graceful shutdown
_term() {
  _echo "Termination signal received. Stopping child processes..."
  if [ -n "${MENTAL_PID:-}" ]; then
    kill -TERM "$MENTAL_PID" 2>/dev/null || true
  fi
  if [ -n "${ADMIN_PID:-}" ]; then
    kill -TERM "$ADMIN_PID" 2>/dev/null || true
  fi
  # allow time to exit
  sleep 2
  exit 0
}
trap _term SIGTERM SIGINT

# wait for a port to respond (uses curl if available)
_wait_for_port() {
  local port=$1
  local tries=0
  local max=20
  if command -v curl >/dev/null 2>&1; then
    until curl -sf "http://127.0.0.1:${port}" >/dev/null 2>&1 || [ $tries -ge $max ]; do
      tries=$((tries+1))
      _echo "Waiting for service on port ${port} (attempt ${tries}/${max})..."
      sleep 1
    done
  else
    _echo "curl not available — sleeping 3s for port ${port}"
    sleep 3
  fi
}

# Probe services that were started
if [ -n "${MENTAL_PID:-}" ]; then
  _wait_for_port "${MENTAL_PORT}"
fi
if [ -n "${ADMIN_PID:-}" ]; then
  _wait_for_port "${ADMIN_PORT}"
fi

# Export proxy targets so proxy.py can read them
export MAIN_TARGET="http://127.0.0.1:${MENTAL_PORT}"
export ADMIN_TARGET="http://127.0.0.1:${ADMIN_PORT}"
export PORT="${PORT}"

_echo "Starting proxy on port ${PORT} -> main:${MAIN_TARGET}, admin:${ADMIN_TARGET}"

# Exec proxy so it becomes PID 1 (proper signal handling by container runtime)
exec python proxy.py
