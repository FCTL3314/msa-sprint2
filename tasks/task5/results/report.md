# Задание 5

Istio 1.31 в Minikube, профиль demo, инъекция sidecar в `default`.

## Что сделано

Две версии - один чарт, два релиза: `booking-service-v1` и `booking-service-v2`, различаются меткой `version`. Service
общий. В v2 включён `ENABLE_FEATURE_X`, фича видна только с заголовком `X-Feature-Enabled: true`. `/ping` отвечает
`pong v1` или `pong v2`, по нему считаю канарейку.

Вход через ingress-шлюз (`gateway.yaml`): port-forward прямо на Service идёт мимо Envoy, и правила на него не действуют.

VirtualService:
- запрос с `x-booking-version: v2` - в v2;
- остальное 90 на v1 и 10 на v2, 3 повтора при 5xx и ошибках соединения.

Fallback. Istio не умеет переключать подмножество при ошибке, повтор идёт в то же подмножество. Поэтому 90% идут не в
подмножество v1, а в сервис целиком, а в DestinationRule стоит `failoverPriority: version=v1`. Пока v1 жив, трафик у
него, нет v1 - уходит в v2. В Envoy это видно как приоритет 0 у v1 и 1 у v2. Если v1 жив, но отвечает 5xx, в v2 уходим
после трёх ошибок подряд, когда `outlierDetection` исключит под.

DestinationRule: подмножества, Circuit Breaking (`connectionPool` и `outlierDetection`: три 5xx подряд - под исключается
на 30 секунд) и `maxRetries`. Сами повторы в Istio задаются только в VirtualService, в DestinationRule есть лишь лимит
на их число, поэтому Retry разнесён по двум файлам.

EnvoyFilter: Lua в ingress-шлюзе. При `X-Feature-Enabled: true` (регистр не важен, ещё `1` и `on`) ставит
`x-booking-version: v2`. Такой же заголовок от клиента вычищает, подделать его нельзя.

## Проверка

Скрипты доработал: адрес в `URL` (у меня 9090 занят сервисом из задания 2, гонял на 19090), канарейка считает ответы,
fallback сам гасит v1.

| Скрипт | Результат |
| :- | :- |
| `check-istio.sh` | istiod и оба шлюза Running, инъекция `enabled` |
| `check-canary.sh` | 89 v1, 11 v2. На 1000 запросов 888 и 112 |
| `check-feature-flag.sh` | 10 из 10 в v2 с фичей, `TRUE` тоже работает, поддельный заголовок не помог |
| `check-fallback.sh` | без подов v1 все 20 запросов отдала v2 с кодом 200 |
