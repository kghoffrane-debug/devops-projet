#!/bin/bash
URL=${1:-http://localhost:5000/health}
RESULT_FILE=${2:-smoke-result.txt}

: > "$RESULT_FILE"

for i in 1 2 3 4 5 6 7 8 9 10; do
  if curl -fs "$URL" > /dev/null; then
    echo "SMOKE TEST: PASSED ($URL)" | tee -a "$RESULT_FILE"
    exit 0
  fi
  echo "Tentative $i/10 : l'app ne repond pas encore..." | tee -a "$RESULT_FILE"
  sleep 2
done

echo "SMOKE TEST: FAILED ($URL)" | tee -a "$RESULT_FILE"
exit 1
