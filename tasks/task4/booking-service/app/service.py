import logging
from datetime import UTC, datetime

import grpc

import booking_pb2
import booking_pb2_grpc
from app import pricing
from app.db import Booking, BookingRepository
from app.events import BookingEvents
from app.monolith import MonolithClient, MonolithUnavailable

log = logging.getLogger(__name__)


class BookingServicer(booking_pb2_grpc.BookingServiceServicer):
    def __init__(self, repository: BookingRepository, events: BookingEvents, monolith: MonolithClient):
        self._repository = repository
        self._events = events
        self._monolith = monolith

    def CreateBooking(self, request, context):
        user_id, hotel_id, promo_code = request.user_id, request.hotel_id, request.promo_code or None
        log.info("CreateBooking: user=%s hotel=%s promo=%s", user_id, hotel_id, promo_code)
        try:
            booking = self._create(user_id, hotel_id, promo_code)
        except pricing.BookingRejected as exc:
            log.info("Booking rejected: %s", exc)
            context.abort(grpc.StatusCode.FAILED_PRECONDITION, str(exc))
        except MonolithUnavailable as exc:
            log.error("%s", exc)
            context.abort(grpc.StatusCode.UNAVAILABLE, str(exc))
        return _to_response(booking)

    def ListBookings(self, request, context):
        bookings = self._repository.list(request.user_id or None)
        return booking_pb2.BookingListResponse(bookings=[_to_response(b) for b in bookings])

    def _create(self, user_id: str, hotel_id: str, promo_code: str | None) -> Booking:
        monolith = self._monolith
        pricing.check_user(monolith.is_user_active(user_id), monolith.is_user_blacklisted(user_id))
        pricing.check_hotel(
            monolith.is_hotel_operational(hotel_id),
            monolith.is_hotel_trusted(hotel_id),
            monolith.is_hotel_fully_booked(hotel_id),
        )
        promo_discount = monolith.promo_discount(promo_code, user_id) if promo_code else None
        discount, price = pricing.calculate_price(monolith.user_status(user_id), promo_discount)

        booking = self._repository.add(Booking(
            user_id=user_id,
            hotel_id=hotel_id,
            promo_code=promo_code,
            discount_percent=discount,
            price=price,
            created_at=datetime.now(UTC),
        ))
        log.info("Booking %s saved: price=%s discount=%s", booking.id, price, discount)
        self._events.booking_created(booking)
        return booking


def _to_response(booking: Booking) -> booking_pb2.BookingResponse:
    # прокси в монолите парсит id через Long.parseLong, а дату через Instant.parse
    created_at = booking.created_at.astimezone(UTC).isoformat().replace("+00:00", "Z")
    return booking_pb2.BookingResponse(
        id=str(booking.id),
        user_id=booking.user_id,
        hotel_id=booking.hotel_id,
        promo_code=booking.promo_code or "",
        discount_percent=booking.discount_percent,
        price=booking.price,
        created_at=created_at,
    )
