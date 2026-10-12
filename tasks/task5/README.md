# booking-service с Istio в Minikube

Копия задания 4, сервис тот же. Отличия: две версии сервиса (v1 и v2) и манифесты Istio в `istio/`.

## Istio

```bash
istioctl install --set profile=demo -y
kubectl label namespace default istio-injection=enabled --overwrite
```

## Развёртывание

```bash
cd tasks/task5
gitlab-ci-local build unit test deploy
```

`deploy` ставит два релиза одного чарта (`values-v1.yaml`, `values-v2.yaml`) и применяет `kubectl apply -f istio/`.
Если в кластере стоит релиз `booking-service` из задания 4, его надо удалить: Service `booking-service` теперь
создаёт релиз v1.

## Проверка

```bash
kubectl -n istio-system port-forward svc/istio-ingressgateway 9090:80
./check-istio.sh
./check-canary.sh
./check-feature-flag.sh
./check-fallback.sh
```

Если порт 9090 занят, port-forward на другой порт и `URL=http://localhost:19090 ./check-canary.sh` и так далее.
