#!/bin/bash

set -e

URL="${URL:-http://localhost:9090}"

echo "▶️ Checking canary release (90% v1, 10% v2)..."

# Посылаем 100 запросов
for i in {1..100}
do
    curl -s "$URL/ping"
done | sort | uniq -c
