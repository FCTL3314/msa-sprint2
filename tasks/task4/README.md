# Развёртывание booking-service в Minikube

Сервис - booking-service из задания 2 (Python, gRPC на 9090), Go-заглушка заменена им. Для Kubernetes в нём есть HTTP
на 8080: `/ping` (проверка живости), `/ready` (готовность), `/feature` (только при `ENABLE_FEATURE_X=true`).

## Что нужно

Docker, Minikube, Helm, kubectl, uv (для unit-тестов), Node.js и `npm install -g gitlab-ci-local`.

```bash
minikube start --driver=docker --memory=8192 --cpus=4
```

## Через пайплайн

```bash
cd tasks/task4
gitlab-ci-local build unit test deploy tag
```

- `build` собирает образы booking-service и booking-history-service, тег - короткий SHA коммита;
- `unit` запускает pytest на расчёт цены;
- `test` поднимает контейнер, проверяет `/ping` и `/ready`, удаляет контейнер;
- `deploy` кладёт образ в Minikube (`minikube image load`) и ставит чарт с `values-staging.yaml`;
- `tag` ставит git-тег `release-<дата-время>`.

Prod: `VALUES_FILE=helm/booking-service/values-prod.yaml` в переменных пайплайна (`--variable`).

## Вручную

```bash
docker build -t booking-service:local booking-service
minikube image load booking-service:local
helm upgrade --install booking-service helm/booking-service \
  -f helm/booking-service/values-staging.yaml --set image.tag=local --wait
```

Реестра образов нет, поэтому `pullPolicy: Never` и `minikube image load`. В бою строку с `minikube image load` убрать,
образ возьмётся из реестра.

## Проверка

```bash
./check-status.sh                       # поды, сервис, релиз helm, curl через port-forward
./check-dns.sh                          # из другого пода: http://booking-service/ping
kubectl port-forward svc/booking-service 8080:80
curl http://localhost:8080/ping
```

Если локальный порт 8080 занят, port-forward на другой порт и `LOCAL_PORT=18080 ./check-status.sh`.

Базы, Kafka и монолита в кластере нет: задание про доставку и обнаружение сервиса. Сервис подключается к ним лениво,
поэтому стартует и отвечает на `/ping` без них. Адреса заданы в `values.yaml` и совпадают с именами из docker compose.
