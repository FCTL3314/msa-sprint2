#!/bin/bash

set -e

LOCAL_PORT="${LOCAL_PORT:-8080}"

echo "▶️ Checking booking-service deployment..."
kubectl get pods -l app=booking-service

echo
echo "▶️ Checking service..."
kubectl get svc booking-service || echo "(No service found)"

echo
echo "▶️ Helm release:"
helm list | grep booking-service || echo "(No release found)"

echo
echo "▶️ Port-forward to test service locally:"
echo "  kubectl port-forward svc/booking-service ${LOCAL_PORT}:80"
echo "  Then in another terminal:"
echo "    curl http://localhost:${LOCAL_PORT}/ping"

echo
echo "▶️ Quick curl (if port-forward already running):"
curl --fail "http://localhost:${LOCAL_PORT}/ping" && echo "✅ Reachable" || echo "❌ Not responding"
