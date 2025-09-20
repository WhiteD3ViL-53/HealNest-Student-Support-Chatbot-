#!/bin/bash
set -e

# Start Streamlit apps in background
streamlit run /app/mental.py --server.port=8501 --server.address=0.0.0.0 &
streamlit run /app/Admin.py --server.port=8502 --server.address=0.0.0.0 &

# Start proxy (routes / to mental, /admin to Admin)
python /app/proxy.py
