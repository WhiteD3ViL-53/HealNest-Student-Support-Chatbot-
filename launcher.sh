#!/usr/bin/env bash 
set -euo pipefail

: "${PORT:=8501}"    # Railway exposes 8501 by default in your service
MENTAL_PORT=${PORT} # run streamlit on the same public PORT

timestamp() { date --utc +'%Y-%m-%dT%H:%M:%SZ'; }
log() { printf '[%s] %s\n' "$(timestamp)" "$*"; }

# If you have GOOGLE_APPLICATION_CREDENTIALS_JSON env, write it to a file (optional)
if [ -n "${GOOGLE_APPLICATION_CREDENTIALS_JSON:-}" ]; then
  log "Writing service account JSON to /tmp/sa.json"
  printf "%s" "$GOOGLE_APPLICATION_CREDENTIALS_JSON" > /tmp/sa.json
  export GOOGLE_APPLICATION_CREDENTIALS=/tmp/sa.json
fi

# Start the mental Streamlit app (foreground so it is PID 1 and logs go to stdout)
if [ -f ./mental.py ]; then
  log "Starting Streamlit mental.py on port ${MENTAL_PORT}"
  exec streamlit run ./mental.py --server.port ${MENTAL_PORT} --server.address 0.0.0.0 --server.headless true
else
  log "ERROR: mental.py not found in /app — sleeping to keep container alive"
  sleep infinity
fi
