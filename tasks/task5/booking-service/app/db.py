import threading
from datetime import datetime

from sqlalchemy import BigInteger, DateTime, Float, String, create_engine, select
from sqlalchemy.orm import DeclarativeBase, Mapped, Session, mapped_column


class Base(DeclarativeBase):
    pass


class Booking(Base):
    __tablename__ = "booking"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    user_id: Mapped[str] = mapped_column(String, index=True)
    hotel_id: Mapped[str] = mapped_column(String)
    promo_code: Mapped[str | None] = mapped_column(String)
    discount_percent: Mapped[float] = mapped_column(Float)
    price: Mapped[float] = mapped_column(Float)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))


class BookingRepository:
    def __init__(self, url: str):
        self._engine = create_engine(url, pool_pre_ping=True)
        self._schema_ready = False
        self._schema_lock = threading.Lock()

    def add(self, booking: Booking) -> Booking:
        self._ensure_schema()
        with Session(self._engine, expire_on_commit=False) as session:
            session.add(booking)
            session.commit()
        return booking

    def list(self, user_id: str | None) -> list[Booking]:
        self._ensure_schema()
        query = select(Booking).order_by(Booking.id)
        if user_id:
            query = query.where(Booking.user_id == user_id)
        with Session(self._engine) as session:
            return list(session.scalars(query))

    def _ensure_schema(self) -> None:
        if self._schema_ready:
            return
        with self._schema_lock:
            if not self._schema_ready:
                Base.metadata.create_all(self._engine)
                self._schema_ready = True
