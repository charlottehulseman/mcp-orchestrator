#!/bin/bash
# Railway start script for Boxonomics

echo "Starting Boxonomics on Railway..."

# Check database exists
if [ ! -f "data/boxing_data.db" ]; then
    echo "ERROR: Database not found!"
    ls -la data/
    exit 1
fi

echo "Database found: $(du -h data/boxing_data.db)"

# Start Streamlit
echo "Starting Streamlit..."
streamlit run frontend/app.py \
    --server.port=${PORT:-8501} \
    --server.address=0.0.0.0 \
    --server.headless=true \
    --server.enableCORS=false \
    --server.enableXsrfProtection=false