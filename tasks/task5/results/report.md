# Задание 5. Управление трафиком с Istio

Задание 4 скопировано в `task5`, сервис тот же - booking-service. Istio 1.31 в Minikube, профиль demo, инъекция
sidecar в namespace `default` включена.

## Что сделано

**Две версии.** Один Helm-чарт ставится двумя релизами: `booking-service-v1` и `booking-service-v2`. Поды отличаются
меткой `version`, Service `booking-service` общий и выбирает поды только по `app`. Различия в `values-v1.yaml` и
`values-v2.yaml`:
- v1: `ENABLE_FEATURE_X=false`, создаёт общий Service;
- v2: `ENABLE_FEATURE_X=true`, но фича показывается только при заголовке `X-Feature-Enabled: true`.

`/ping` отвечает `pong v1` или `pong v2`, без этого канарейку не посчитать. Пайплайн из задания 4 ставит оба релиза и
применяет манифесты из `istio/`.

**Вход - через ingress-шлюз** (`istio/gateway.yaml`). `kubectl port-forward` прямо на Service идёт мимо Envoy, и
правила маршрутизации на такой трафик не действуют. Скрипты ходят на
`kubectl -n istio-system port-forward svc/istio-ingressgateway <порт>:80`.

**VirtualService** (`virtual-service.yaml`), маршруты по порядку:
1. фича-флаг: служебный заголовок `x-booking-version: v2` → подмножество v2. Заголовок ставит EnvoyFilter;
2. канарейка: 90% на `booking-service` без подмножества, 10% на подмножество v2. Повторы: 3 попытки при 5xx и ошибках
соединения, по 2 секунды, общий таймаут 10 секунд.

**Fallback.** Здесь самое интересное. Istio не умеет переключать маршрут на другое подмножество, если первое ответило
ошибкой: повтор идёт в то же подмножество. Поэтому 90% идут не в подмножество v1, а в сервис целиком, где поды обеих
версий. В DestinationRule для этого кластера задан `failoverPriority: version=v1`: поды v1 получают приоритет 0, поды
v2 - приоритет 1. Пока v1 доступен, весь этот трафик идёт в v1. Когда подов v1 нет или они исключены за ошибки, трафик
переходит к v2. Это видно в конфигурации Envoy в шлюзе:

```
10.244.0.20 priority=0 health=HEALTHY   (v1)
10.244.0.19 priority=1 health=HEALTHY   (v2)
```

Ограничение: если v1 жив, но начал отвечать 5xx, первые ошибочные запросы повторяются и могут снова попасть в v1. В v2
трафик уходит после третьей ошибки подряд, когда `outlierDetection` исключает под v1 на 30 секунд. Если же под v1
погашен, переключение мгновенное.

**DestinationRule** (`destination-rule.yaml`). Подмножества v1 и v2, Circuit Breaking:
- `connectionPool`: до 100 соединений, до 50 запросов в очереди, сверх этого запросы сразу отклоняются, а не копятся;
- `outlierDetection`: под с тремя 5xx подряд исключается из балансировки на 30 секунд;
- `maxRetries: 3`: сколько повторов может одновременно идти в сервис.

Про Retry: в задании сказано настроить его через DestinationRule, но политика повторов в Istio задаётся только в
VirtualService. В DestinationRule есть `maxRetries` - ограничение на число одновременных повторов, оно не даёт
повторам превратиться в лавину, когда сервису и так плохо. Поэтому повторы описаны в VirtualService, а их лимит - в
DestinationRule.

**EnvoyFilter** (`envoy-filter.yaml`). Lua-фильтр в ingress-шлюзе: если `X-Feature-Enabled` равен `true` (без учёта
регистра, ещё `1` и `on`), ставит `x-booking-version: v2` и сбрасывает кеш маршрута, чтобы VirtualService выбрал
маршрут заново. Простой match по `X-Feature-Enabled` в VirtualService тоже сработал бы. Отдельный слой даёт две вещи:
флаг приводится к одному виду, а служебный заголовок от клиента вычищается, подделать его нельзя. У фильтра явный
приоритет: без него `istioctl analyze` предупреждает, что порядок применения вставки не гарантирован. Предупреждение
IST0133 остаётся, его Istio выдаёт на любой EnvoyFilter.

## Проверка

Скрипты доработаны:
- адрес шлюза вынесен в переменную `URL` (по умолчанию `localhost:9090`). У меня порт 9090 занят booking-service из
задания 2, поэтому скрипты гонялись с `URL=http://localhost:19090`;
- `check-canary.sh` считает ответы по версиям;
- `check-feature-flag.sh` дополнительно проверяет флаг в другом регистре и то, что поддельный `x-booking-version` от
клиента игнорируется;
- `check-fallback.sh` сам гасит поды v1, шлёт 20 запросов и возвращает v1.

| Скрипт | Результат |
| :- | :- |
| `check-istio.sh` | istiod и оба шлюза Running, инъекция `enabled` |
| `check-canary.sh` | 89 v1, 11 v2. На 1000 запросов: 888 и 112 |
| `check-feature-flag.sh` | 10 из 10 в v2 с фичей, `TRUE` тоже работает, поддельный заголовок проигнорирован |
| `check-fallback.sh` | без подов v1 все 20 запросов обслужила v2, все с кодом 200 |

## Что в папке

- `report.md`;
- `values-v1.yaml`, `values-v2.yaml`;
- `virtual-service.yaml`, `destination-rule.yaml`, `envoy-filter.yaml`;
- `check-istio.log`, `check-canary.log`, `check-feature-flag.log`, `check-fallback.log`.
