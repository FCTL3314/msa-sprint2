import json
import logging
import os
import time

import psycopg
from confluent_kafka import Consumer, KafkaError

log = logging.getLogger("booking-history-service")

SCHEMA = """
CREATE TABLE IF NOT EXISTS booking_history (
    event_id         UUID PRIMARY KEY,
    booking_id       BIGINT NOT NULL,
    user_id          TEXT NOT NULL,
    hotel_id         TEXT NOT NULL,
    promo_code       TEXT,
    discount_percent DOUBLE PRECISION NOT NULL,
    price            DOUBLE PRECISION NOT NULL,
    created_at       TIMESTAMPTZ NOT NULL,
    received_at      TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE OR REPLACE VIEW stats_by_user AS
    SELECT user_id, count(*) AS bookings, sum(price) AS revenue
    FROM booking_history GROUP BY user_id;

CREATE OR REPLACE VIEW stats_by_hotel AS
    SELECT hotel_id, count(*) AS bookings, sum(price) AS revenue
    FROM booking_history GROUP BY hotel_id;

CREATE OR REPLACE VIEW stats_by_day AS
    SELECT created_at::date AS day, count(*) AS bookings, sum(price) AS revenue
    FROM booking_history GROUP BY created_at::date;
"""

INSERT = """
INSERT INTO booking_history
    (event_id, booking_id, user_id, hotel_id, promo_code, discount_percent, price, created_at)
VALUES
    (%(event_id)s, %(booking_id)s, %(user_id)s, %(hotel_id)s, %(promo_code)s, %(discount_percent)s,
     %(price)s, %(created_at)s)
ON CONFLICT (event_id) DO NOTHING
"""


def connect(url: str) -> psycopg.Connection:
    for attempt in range(30):
        try:
            return psycopg.connect(url, autocommit=True)
        except psycopg.OperationalError:
            log.info("Waiting for the database, attempt %s", attempt + 1)
            time.sleep(2)
    raise RuntimeError("Database is unavailable")


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")

    db = connect(os.environ["DATABASE_URL"])
    db.execute(SCHEMA)

    topic = os.getenv("KAFKA_TOPIC", "booking.created")
    consumer = Consumer({
        "bootstrap.servers": os.environ["KAFKA_BOOTSTRAP_SERVERS"],
        "group.id": "booking-history",
        "auto.offset.reset": "earliest",
        "enable.auto.commit": False,
        "allow.auto.create.topics": True,
        "topic.metadata.refresh.interval.ms": 5000,
    })
    consumer.subscribe([topic])
    log.info("Listening to %s", topic)

    while True:
        message = consumer.poll(1.0)
        if message is None:
            continue
        if message.error():
            if message.error().code() != KafkaError.UNKNOWN_TOPIC_OR_PART:
                log.error("Kafka error: %s", message.error())
            continue

        event = json.loads(message.value())
        db.execute(INSERT, event)
        consumer.commit(message=message, asynchronous=False)
        log.info("History saved: booking %s, user %s, hotel %s", event["booking_id"], event["user_id"], event["hotel_id"])


if __name__ == "__main__":
    main()
