# Задание 4

## Сервис

Go-заглушку заменил своим booking-service. Рядом с gRPC добавил HTTP на 8080: `/ping` для проб, `/ready` (503, пока
gRPC не поднялся) и `/feature` при `ENABLE_FEATURE_X=true`. Dockerfile есть у обоих сервисов, в кластер ставится только
booking-service.

Что пришлось поправить для Kubernetes:
- подключения к базе и Kafka ленивые: в кластере их нет, а под должен стартовать;
- обработчик SIGTERM. Без него Python с PID 1 игнорировал сигнал, и под при каждом обновлении висел в Terminating 30
секунд.

## Helm

Пробы по `/ping`, ClusterIP 80 → 8080, все поля values из задания. В шаблоне пода аннотация `rollme`: образ грузится под
тем же тегом, и без неё `helm upgrade` не перезапускал поды. Поймал на втором прогоне.

| | staging | prod |
| :- | :- | :- |
| replicaCount | 1 | 2 |
| ENABLE_FEATURE_X | true | false |
| requests | 50m / 96Mi | 100m / 128Mi |
| limits | 250m / 192Mi | 500m / 256Mi |

В prod две реплики, чтобы перезапуск пода не останавливал бронирование. Prod проверил отдельным деплоем.

## Пайплайн

build, unit, test, deploy, tag. unit - отдельная стадия с pytest, 11 тестов на расчёт цены. Тег образа - SHA коммита.
В `build.log` прогон без tag: эта стадия ставит git-тег.

## DNS

`check-dns.sh` из busybox в кластере делает `wget http://booking-service/ping`. Вывод привёл к формату из задания. В
`check-status.sh` добавил `LOCAL_PORT`, у меня 8080 занят.
