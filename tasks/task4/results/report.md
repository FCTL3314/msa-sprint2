# Задание 4. Docker, Helm, CI/CD, DNS

## Сервис

Go-заглушку заменил своим booking-service из задания 2. Рядом с gRPC (9090) добавлен HTTP на 8080:
- `/ping` отвечает `pong`, на него смотрят обе пробы;
- `/ready` отвечает `ready`, когда gRPC-сервер запущен, до этого 503;
- `/feature` есть только при `ENABLE_FEATURE_X=true`, так флаг меняет поведение.

Что пришлось поправить в самом сервисе, чтобы он нормально жил в Kubernetes:
- подключения к базе и Kafka создаются при первом обращении, а не на старте. В кластере их нет, а под должен
стартовать и проходить пробы;
- обработка SIGTERM. Python с PID 1 без обработчика игнорирует сигнал, и под при каждом обновлении висел в
`Terminating` 30 секунд до принудительного завершения. Теперь gRPC-сервер останавливается сам, замена пода занимает
несколько секунд.

Dockerfile есть у обоих сервисов: `booking-service/` и `booking-history-service/`, пайплайн собирает оба. В кластер
ставится только booking-service, как и требует задание.

## Helm-чарт

- Deployment: пробы `livenessProbe` и `readinessProbe` по `/ping`, параметры проб в values.
- Service ClusterIP, порт 80 → 8080, имя `booking-service`.
- Из values: `replicaCount`, `image.name`, `image.tag`, `image.pullPolicy`, `env[]`, `resources`, `ENABLE_FEATURE_X`.
- В шаблоне пода аннотация со случайным значением. Образ грузится в Minikube под тем же тегом, без неё
`helm upgrade` не перезапускает поды и в кластере остаётся старый код. Это я поймал на втором прогоне пайплайна.

| | staging | prod |
| :- | :- | :- |
| replicaCount | 1 | 2 |
| ENABLE_FEATURE_X | true | false |
| requests | 50m / 96Mi | 100m / 128Mi |
| limits | 250m / 192Mi | 500m / 256Mi |

В prod две реплики, чтобы перезапуск одного пода не останавливал бронирование. Prod проверил отдельным деплоем: две
реплики, `ENABLE_FEATURE_X=false`.

## Пайплайн

Стадии `build`, `unit`, `test`, `deploy`, `tag`, запуск `gitlab-ci-local build unit test deploy tag`. Задачи без
`image:`, поэтому выполняются прямо на машине. `unit` - отдельная стадия с pytest: 11 тестов на расчёт цены и
проверки, включая особенность монолита со скидкой суммой. Тег образа - короткий SHA коммита.

## DNS

`check-dns.sh` поднимает busybox в кластере и делает `wget http://booking-service/ping`, адрес даёт DNS кластера.
Скрипт доработан: вывод в формате из задания, удаление пода от прерванного запуска, первая строка ответа (kubectl
иногда печатает вывод пода дважды).

```
[INFO] Running in-cluster DNS test...
[INFO] DNS Response: pong
[PASS] DNS test succeeded
```

`check-status.sh` получил переменную `LOCAL_PORT`: на моей машине 8080 занят, и curl уходил не в сервис.

## Что в папке

- `report.md`, `values-staging.yaml`, `values-prod.yaml`, `.gitlab-ci.yml`;
- `build.log` - вывод `gitlab-ci-local` по стадиям build, unit, test, deploy;
- `kubectl-get.txt` - `kubectl get pods` и `kubectl get services`;
- `images.txt` - `docker image ls` и `minikube image list`;
- `curl-ping.png`, `check-dns.png`, `check-status.png` - скриншоты.
