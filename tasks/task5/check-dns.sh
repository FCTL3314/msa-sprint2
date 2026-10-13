#!/bin/bash

set -e

echo "[INFO] Running in-cluster DNS test..."

kubectl delete pod dns-test --ignore-not-found >/dev/null

response=$(kubectl run dns-test --rm -i --quiet \
  --image=busybox \
  --labels=sidecar.istio.io/inject=false \
  --restart=Never \
  -- wget -qO- http://booking-service/ping 2>/dev/null || true)
# kubectl иногда печатает вывод пода дважды
response=$(echo "$response" | head -n 1)

echo "[INFO] DNS Response: ${response}"

if [[ "$response" == pong* ]]; then
  echo "[PASS] DNS test succeeded"
else
  echo "[FAIL] DNS test failed"
  exit 1
fi
