#!/bin/bash

LABEL="${1:-test}"
CHURN="${2:-}"
OUT="results.txt"

[ "$CHURN" ] && FLAG="--disable-keepalive" || FLAG=""

for c in 100 500 1000 2000 5000; do
    echo "[$(date +%H:%M:%S)] Clearing rate limit key..."
    redis-cli DEL "rate_limit:ai:127.0.0.1"
    
    echo "[$(date +%H:%M:%S)] Running $LABEL @ $c (churn: ${CHURN:-off})"
    
    echo "=== $LABEL | $c connections | churn: ${CHURN:-off} ===" | tee -a "$OUT"
    oha -z 30s -c "$c" --no-tui $FLAG \
        -m POST \
        -d '{"query": "This is my grand query"}' \
        http://localhost:8000/models/auto 2>&1 | tee -a "$OUT"
    
    echo "" | tee -a "$OUT"
    echo "[$(date +%H:%M:%S)] Done with $c"
    echo ""
    
    sleep 2
done

echo "[$(date +%H:%M:%S)] All done for $LABEL"
