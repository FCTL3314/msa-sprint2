import logging
import os
import signal
from concurrent import futures

import grpc
from grpc_reflection.v1alpha import reflection

import booking_pb2
import booking_pb2_grpc
from app import health
from app.db import BookingRepository
from app.events import BookingEvents
from app.monolith import MonolithClient
from app.service import BookingServicer

log = logging.getLogger("booking-service")


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")

    health.start_http_server(int(os.getenv("HTTP_PORT", "8080")))

    servicer = BookingServicer(
        repository=BookingRepository(
            os.getenv("DATABASE_URL", "postgresql+psycopg://booking:booking@booking-db:5432/booking")
        ),
        events=BookingEvents(
            os.getenv("KAFKA_BOOTSTRAP_SERVERS", "kafka:9092"), os.getenv("KAFKA_TOPIC", "booking.created")
        ),
        monolith=MonolithClient(os.getenv("MONOLITH_URL", "http://hotelio-monolith:8080")),
    )

    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    booking_pb2_grpc.add_BookingServiceServicer_to_server(servicer, server)
    service_name = booking_pb2.DESCRIPTOR.services_by_name["BookingService"].full_name
    reflection.enable_server_reflection([service_name, reflection.SERVICE_NAME], server)

    port = os.getenv("GRPC_PORT", "9090")
    server.add_insecure_port(f"[::]:{port}")
    server.start()
    health.ready.set()
    # без обработчика python с PID 1 игнорирует SIGTERM и под висит в Terminating
    signal.signal(signal.SIGTERM, lambda *_: server.stop(grace=5))
    log.info("gRPC server is listening on %s, HTTP on %s", port, os.getenv("HTTP_PORT", "8080"))
    server.wait_for_termination()


if __name__ == "__main__":
    main()
