# Задание 3

Запуск: сначала стек задания 2, потом `docker compose up -d --build` в `tasks/task3`. Шлюз на http://localhost:4000.

## Что сделано

- Папку `gateway` переименовал в `apollo-gateway`, как в структуре задания. Шлюз собирает схему из трёх подграфов.
Заголовки клиента в подграфы он сам не передаёт, хотя в подсказке написано обратное, поэтому `userid` пробрасываю явно.
- booking-subgraph берёт брони по gRPC у booking-service из задания 2. ACL: если `userid` не совпадает с `userId`,
отдаю `FORBIDDEN`. Пустой список не отдаю, чтобы клиент отличал «нет броней» от «нельзя смотреть».
- hotel-subgraph берёт отели у монолита по REST через DataLoader: на весь запрос по одному вызову на уникальный отель.
Пакетного эндпоинта у монолита нет. Имени и звёзд у отеля в монолите тоже нет, `name` беру из описания, `stars` из
рейтинга.
- promocode-subgraph новый. `discountPercent` переехал в него через `@override`, `promoCode` он получает через
`@requires`. Срок `validUntil` проверяет, монолит этого не делал. `activePromoCodes` не делал: в задании он для примера,
а списка промокодов у монолита нет.
- Стек вызовов в ответах с ошибкой отключил.

## Проверка

Пользователя `user1` из задания в данных нет, взял `test-user-3`: у него две брони в одном отеле.

```graphql
query {
  bookingsByUser(userId: "test-user-3") {
    id
    promoCode
    hotel { name city }
    discountPercent
    discountInfo { isValid originalDiscount finalDiscount description }
  }
}
```

- с `userid: test-user-3` - брони с отелем и скидкой, `success.png`;
- с `userid: test-user-2` - `FORBIDDEN`, `deny.png`.

На этот запрос hotel-subgraph сходил в монолит один раз: `hotel batch: 1 unique ids [test-hotel-1]`. Логи
booking-subgraph после двух запросов в `booking-subgraph.log`.
