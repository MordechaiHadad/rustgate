#!/bin/bash

LABEL="${1:-test}"
CHURN="${2:-}"  # leave empty for no churn, set to anything for churn
OUT="results.txt"

[ "$CHURN" ] && FLAG="--disable-keepalive" || FLAG=""

for c in 100 500 1000 2000 5000; do
    redis-cli FLUSHALL
    redis-cli SAVE
    sleep 8
    
    echo "=== $LABEL | $c connections | churn: ${CHURN:-off} ===" >> "$OUT"
    oha -z 30s -c "$c" --no-tui $FLAG \
        -m POST \
        -d '{"query": "This is my grand query"}' \
        http://localhost:8000/models/auto >> "$OUT" 2>&1
    echo "" >> "$OUT"
done
