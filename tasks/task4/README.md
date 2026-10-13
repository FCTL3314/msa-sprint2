# booking-service в Minikube

Сервис из задания 2 вместо Go-заглушки. HTTP на 8080: `/ping`, `/ready` и `/feature` при `ENABLE_FEATURE_X=true`.

```bash
minikube start --driver=docker --memory=8192 --cpus=4
gitlab-ci-local build unit test deploy tag
```

Стадии: сборка обоих образов, pytest, проверка `/ping` в контейнере, `minikube image load` и `helm upgrade` с
`values-staging.yaml`, git-тег. Для prod: `--variable VALUES_FILE=helm/booking-service/values-prod.yaml`.

Вручную:

```bash
docker build -t booking-service:local booking-service
minikube image load booking-service:local
helm upgrade --install booking-service helm/booking-service \
  -f helm/booking-service/values-staging.yaml --set image.tag=local --wait
```

Проверка:

```bash
kubectl port-forward svc/booking-service 8080:80
curl http://localhost:8080/ping
./check-dns.sh
./check-status.sh
```

Если 8080 занят, port-forward на другой порт и `LOCAL_PORT=<порт> ./check-status.sh`.

Базы, Kafka и монолита в кластере нет, сервис подключается к ним лениво и стартует без них.
