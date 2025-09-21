#!/usr/bin/env bash
set -euo pipefail

echo "=== DIAGNOSTIC ADMIN LAUNCHER START ==="

# Show working dir and files
echo "--- PWD ---"
pwd
echo "--- FILES (ls -al) ---"
ls -al
echo "--- TREE (maxdepth 2) ---"
find . -maxdepth 2 -type f | sort

# Check Python version & pip
echo "--- PYTHON INFO ---"
python --version || true
pip --version || true
pip list || true

# Try to show Admin.py specifically
if [ -f "./Admin.py" ]; then
  echo "FOUND Admin.py ✅"
else
  echo "Admin.py NOT FOUND ❌"
fi

# Run Admin.py with Streamlit directly
echo "--- Starting Admin.py with Streamlit ---"
exec streamlit run ./Admin.py --server.port=8080 --server.address=0.0.0.0 --server.headless true
