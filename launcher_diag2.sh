#!/usr/bin/env bash
set -e

echo "=== diagnostic start ==="
echo "PWD: $(pwd)"
echo "LS /app"
ls -al /app || true

echo "=== attempt start Admin in foreground (captures error) ==="
# Try starting Admin in foreground so Streamlit output appears in build logs
# Timeout after 8 seconds to avoid blocking the deploy forever
timeout 8 bash -lc 'streamlit run ./Admin.py --server.port 8502 --server.address 0.0.0.0 --server.headless true' || echo "Admin start finished (or timed out)"

echo "=== ps aux ==="
ps aux | sed -n '1,200p' || true

echo "=== try curl local ports ==="
curl -sS http://127.0.0.1:8502/ -m 3 | sed -n '1,60p' || echo "8502 not responding"
curl -sS http://127.0.0.1:8501/ -m 3 | sed -n '1,60p' || echo "8501 not responding"

sleep 3
echo "=== diagnostic end ==="
