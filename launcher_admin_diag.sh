#!/usr/bin/env bash
set -e

echo "=== PWD ==="
pwd

echo "=== ls /app ==="
ls -al /app || true

echo "=== show top of Admin.py ==="
if [ -f ./Admin.py ]; then
  sed -n '1,120p' ./Admin.py
else
  echo "Admin.py not found in /app"
fi

echo "=== attempt to start Admin in foreground (8s timeout) ==="
# Run streamlit in foreground for a short time to capture startup output/errors
timeout 8 bash -lc 'streamlit run ./Admin.py --server.port 8602 --server.address 0.0.0.0 --server.headless true' || echo "Admin start finished or timed out"

echo "=== try curl 127.0.0.1:8602 ==="
curl -sS http://127.0.0.1:8602/ -m 3 | sed -n '1,80p' || echo "8602 not responding"

echo "=== END DIAG ==="
