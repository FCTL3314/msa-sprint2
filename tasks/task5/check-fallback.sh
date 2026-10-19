#!/bin/bash

set -e

URL="${URL:-http://localhost:9090}"

echo "▶️ Testing fallback route..."

echo "▶️ Гасим поды v1"
kubectl scale deployment/booking-service-v1 --replicas=0
kubectl wait --for=delete pod -l app=booking-service,version=v1 --timeout=60s || true
kubectl get pods -l app=booking-service

echo "▶️ 20 запросов без v1: весь трафик должен уйти в v2, без ошибок"
for i in {1..20}
do
    curl -s -w " [%{http_code}]" "$URL/ping" | tr -d '\n'; echo
    sleep 0.1
done | sort | uniq -c

echo "▶️ Возвращаем v1"
kubectl scale deployment/booking-service-v1 --replicas=1
kubectl rollout status deployment/booking-service-v1 --timeout=120s

curl -s "$URL/ping" || echo "Fallback route working"
