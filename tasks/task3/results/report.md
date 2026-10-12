# Задание 3. Личный кабинет на GraphQL Federation

Запуск: сначала стек задания 2 (`tasks/task2`, `docker compose up -d --build`), потом здесь
`docker compose up -d --build`. Все модули в сети `hotelio-net`, шлюз на http://localhost:4000.

## Что изменено

**apollo-gateway** (папка `gateway` переименована под структуру из задания)
- Схему собирает `IntrospectAndCompose` из трёх подграфов: `booking-subgraph`, `hotel-subgraph`, `promocode-subgraph`.
Имена важны: на `booking-subgraph` ссылается `@override`.
- Шлюз сам не передаёт заголовки клиента в подграфы, хотя в подсказке к заданию написано обратное. Добавил
`RemoteGraphQLDataSource`, который пробрасывает `userid`, без этого ACL не работает.
- `restart: on-failure`: шлюз падает, если на старте какой-то подграф ещё не поднялся.
- Стек вызовов в ответах с ошибкой отключён, в шлюзе и в подграфах.

**booking-subgraph**
- Заглушка заменена на gRPC-вызов `ListBookings` в booking-service из задания 2, по тому же `booking.proto`.
- Поля `id`, `userId`, `hotelId`, `promoCode`, `discountPercent`, плюс `hotel` - ссылка на `Hotel` из hotel-subgraph.
`discountPercent` стал `Float`, как в базе.
- ACL: если заголовок `userid` не совпадает с запрошенным `userId` или его нет, запрос отклоняется с кодом
`FORBIDDEN`. Отказ вместо пустого списка выбрал, чтобы клиент отличал «нет броней» от «нельзя смотреть». Пока нет API
Gateway с токенами, заголовку приходится верить на слово, это временное решение.

**hotel-subgraph**
- `__resolveReference` и новый `hotelsByIds(ids)` идут через DataLoader. Он создаётся на каждый запрос: собирает id
отелей одного запроса в один вызов, убирает повторы и кеширует результат до конца запроса.
- Источник - REST монолита `/api/hotels/{id}`. Пакетного эндпоинта у монолита нет, поэтому в монолит уходит по запросу
на каждый уникальный отель, а не на каждую бронь. Сверху короткий кеш на 60 секунд между запросами: отели меняются
редко. В To-Be у сервиса отелей появится выдача сразу по списку id.
- У отеля в монолите нет имени и звёзд, хотя в описании API они есть. `name` берётся из `description`, `stars` -
округлённый `rating`.

**promocode-subgraph** (новый)
- Перенесены типы промокодов: `Booking` расширен полями `discountPercent` и `discountInfo`, добавлен `DiscountInfo` и
запрос `validatePromoCode`.
- `discountPercent` резолвится здесь: `@override(from: "booking-subgraph")`. Значение - скидка промокода после
проверки, а не то, что лежит в бронировании. `promoCode` подграф получает через `@requires(fields: "promoCode")`.
- Проверка строже, чем в монолите: кроме флага `expired` смотрим срок `validUntil`. Новая логика промокодов пишется
уже здесь. `TESTCODE-OLD` даёт `isValid: false`, `finalDiscount: 0`.
- `applicableHotels` пустой: привязки промокодов к отелям в данных нет.
- `activePromoCodes` не сделал. В задании он «для примера», списка промокодов у монолита нет, а дорабатывать
монолит по плану миграции нельзя.

## Проверка

В запросе из задания `userId: "user1"`, но такого пользователя в тестовых данных нет. Использую `test-user-3`: у него
две брони в одном отеле, на них видно и промокод, и работу DataLoader.

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

- заголовок `userid: test-user-3` - две брони с отелем и скидкой, скриншот `success.png`;
- заголовок `userid: test-user-2` - `FORBIDDEN`, скриншот `deny.png`.

Лог hotel-subgraph на этот запрос - один запрос в монолит на две брони:
```
hotel batch: 1 unique ids [test-hotel-1]
```

## Что в папке

- `report.md` - этот отчёт;
- `docker-ps.txt` - контейнеры заданий 2 и 3;
- `success.png`, `deny.png` - успешный вызов и отказ по ACL в Apollo Sandbox;
- `booking-subgraph.log` - лог booking-subgraph после двух запросов: разрешённого и отклонённого.
