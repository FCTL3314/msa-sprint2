# booking-service с Istio

Копия задания 4 плюс две версии сервиса и манифесты в `istio/`.

```bash
istioctl install --set profile=demo -y
kubectl label namespace default istio-injection=enabled --overwrite
gitlab-ci-local build unit test deploy
```

`deploy` ставит релизы `booking-service-v1` и `booking-service-v2` и применяет `istio/`. Релиз `booking-service` из
задания 4 перед этим удалить, Service теперь создаёт v1.

```bash
kubectl -n istio-system port-forward svc/istio-ingressgateway 9090:80
./check-istio.sh
./check-canary.sh
./check-feature-flag.sh
./check-fallback.sh
```

Если 9090 занят: `URL=http://localhost:<порт> ./check-canary.sh` и так далее.
