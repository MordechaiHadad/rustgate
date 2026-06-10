#!/bin/bash

# Configuration
REMOTE_HOST="${1:?Error: Please provide the remote desktop IP address (e.g., 10.0.0.6)}"
LABEL="${2:-test}"
CHURN="${3:-}"
OUT="results.txt"

# Port configurations
HTTP_PORT="8000"
REDIS_PORT="6379"

[ "$CHURN" ] && FLAG="--disable-keepalive" || FLAG=""

echo "================================================="
echo "Target Machine IP: $REMOTE_HOST"
echo "================================================="

for c in 100 500 1000 2000 5000 10000; do
    echo "[$(date +%H:%M:%S)] Running $LABEL @ $c (churn: ${CHURN:-off})"
    
    echo "=== $LABEL | $c connections | churn: ${CHURN:-off} ===" | tee -a "$OUT"
    
    # Executes the load test against the remote FastAPI endpoint
    oha -z 30s -c "$c" --no-tui $FLAG \
        -m POST \
        -d '{"query": "This is my grand query"}' \
        "http://${REMOTE_HOST}:${HTTP_PORT}/models/auto" 2>&1 | tee -a "$OUT"
    
    echo "" | tee -a "$OUT"
    echo "[$(date +%H:%M:%S)] Done with $c"
    echo ""
    
    echo "[$(date +%H:%M:%S)] Waiting for 1:10 minute"
    sleep 70
done

echo "[$(date +%H:%M:%S)] All done for $LABEL"
