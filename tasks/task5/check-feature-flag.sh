#!/bin/bash

set -e

URL="${URL:-http://localhost:9090}"

echo "▶️ Проверка Feature Flag (X-Feature-Enabled: true)..."

# Отправляем запрос с заголовком, чтобы маршрутизировать трафик на `v2`
for i in {1..10}
do
    curl -s -H "X-Feature-Enabled: true" "$URL/ping"
done | sort | uniq -c

echo "▶️ Тот же флаг в другом регистре и служебный заголовок от клиента (должен игнорироваться)..."
curl -s -H "X-Feature-Enabled: TRUE" "$URL/ping"
for i in {1..20}
do
    curl -s -H "x-booking-version: v2" "$URL/ping"
done | sort | uniq -c
