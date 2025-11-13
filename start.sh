#!/bin/bash
# Railway start script for Boxonomics

set -e

echo "Starting Boxonomics on Railway..."
echo "PORT environment variable: ${PORT:-not set}"

# Check database exists
if [ ! -f "data/boxing_data.db" ]; then
    echo "ERROR: Database not found!"
    exit 1
fi

echo "Database found: $(du -h data/boxing_data.db)"

# Railway sets PORT - we MUST use it
# If PORT is not set, default to 8501
STREAMLIT_PORT="${PORT:-8501}"

echo "Starting Streamlit on port $STREAMLIT_PORT..."

exec streamlit run frontend/app.py \
    --server.port=$STREAMLIT_PORT \
    --server.address=0.0.0.0 \
    --server.headless=true \
    --server.enableCORS=false \
    --server.enableXsrfProtection=false