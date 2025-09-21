#!/usr/bin/env bash
set -euo pipefail

: "${PORT:=8501}"

echo "[launcher_admin] Starting Admin.py on port ${PORT}"
exec streamlit run ./Admin.py --server.port ${PORT} --server.address 0.0.0.0 --server.headless true
