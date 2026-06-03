#!/bin/bash

LABEL="${1:-test}"
CHURN="${2:-}"
OUT="results.txt"

[ "$CHURN" ] && FLAG="--disable-keepalive" || FLAG=""

for c in 100 500 1000 2000 5000; do
    echo "[$(date +%H:%M:%S)] Flushing Redis..."
    redis-cli FLUSHALL
    redis-cli KEYS "rate_limit:*" | xargs redis-cli DEL
    redis-cli SAVE

    # Verify DBSIZE is 0 before proceeding
    echo "[$(date +%H:%M:%S)] Verifying Redis is empty..."
    for i in {1..10}; do
        DBSIZE=$(redis-cli DBSIZE | tr -d '\r\n')
        if [ "$DBSIZE" = "0" ]; then
            echo "[$(date +%H:%M:%S)] DBSIZE confirmed: 0"
            break
        fi
        echo "[$(date +%H:%M:%S)] DBSIZE is $DBSIZE, waiting 1s (attempt $i/10)..."
        sleep 1
    done

    # Final check
    FINAL=$(redis-cli DBSIZE | tr -d '\r\n')
    if [ "$FINAL" != "0" ]; then
        echo "[$(date +%H:%M:%S)] WARNING: DBSIZE is still $FINAL — your app may be writing keys. Proceeding anyway."
    fi

    echo "[$(date +%H:%M:%S)] Waiting 8s..."
    sleep 8

    echo "[$(date +%H:%M:%S)] Running $LABEL @ $c connections (churn: ${CHURN:-off})"

    echo "=== $LABEL | $c connections | churn: ${CHURN:-off} ===" | tee -a "$OUT"
    oha -z 30s -c "$c" --no-tui $FLAG \
        -m POST \
        -d '{"query": "This is my grand query"}' \
        http://localhost:8000/models/auto 2>&1 | tee -a "$OUT"

    echo "" | tee -a "$OUT"
    echo "[$(date +%H:%M:%S)] Done with $c"
    echo ""
done

echo "[$(date +%H:%M:%S)] All done for $LABEL"
