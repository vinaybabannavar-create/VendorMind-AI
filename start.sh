#!/bin/bash
set -e

echo "Starting VendorMind API (internal, port 8080)..."
uvicorn api.main:app --host 127.0.0.1 --port 8080 &

# Wait for the API to actually be ready before starting the dashboard,
# rather than a fixed sleep — avoids race conditions on slow cold starts.
echo "Waiting for API health check..."
for i in $(seq 1 30); do
    if curl -sf http://127.0.0.1:8080/health > /dev/null 2>&1; then
        echo "API is up."
        break
    fi
    sleep 1
done

echo "Starting Streamlit dashboard (public, port ${PORT:-8501})..."
streamlit run ui/app.py \
    --server.port="${PORT:-8501}" \
    --server.address=0.0.0.0 \
    --server.headless=true \
    --browser.gatherUsageStats=false
