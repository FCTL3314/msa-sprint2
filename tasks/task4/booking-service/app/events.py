import json
import logging
import uuid

from confluent_kafka import KafkaError, Message, Producer

from app.db import Booking

log = logging.getLogger(__name__)


class BookingEvents:
    def __init__(self, bootstrap_servers: str, topic: str):
        self._bootstrap_servers = bootstrap_servers
        self._topic = topic
        self._producer: Producer | None = None

    def booking_created(self, booking: Booking) -> None:
        event = {
            "event_id": str(uuid.uuid4()),
            "event_type": "BookingCreated",
            "booking_id": booking.id,
            "user_id": booking.user_id,
            "hotel_id": booking.hotel_id,
            "promo_code": booking.promo_code,
            "discount_percent": booking.discount_percent,
            "price": booking.price,
            "created_at": booking.created_at.isoformat(),
        }
        producer = self._get_producer()
        producer.produce(self._topic, key=str(booking.id), value=json.dumps(event), on_delivery=_log_delivery)
        if producer.flush(5) > 0:
            log.warning("BookingCreated for booking %s is not delivered yet", booking.id)

    def _get_producer(self) -> Producer:
        if self._producer is None:
            self._producer = Producer({"bootstrap.servers": self._bootstrap_servers, "acks": "all"})
        return self._producer


def _log_delivery(error: KafkaError | None, message: Message) -> None:
    if error is not None:
        log.error("BookingCreated delivery failed: %s", error)
    else:
        log.info("BookingCreated sent: booking %s, partition %s", message.key().decode(), message.partition())
