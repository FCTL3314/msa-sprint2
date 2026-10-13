BASE_PRICE = 100.0
VIP_BASE_PRICE = 80.0


class BookingRejected(Exception):
    pass


def check_user(active: bool, blacklisted: bool) -> None:
    if not active:
        raise BookingRejected("User is inactive")
    if blacklisted:
        raise BookingRejected("User is blacklisted")


def check_hotel(operational: bool, trusted: bool, fully_booked: bool) -> None:
    if not operational:
        raise BookingRejected("Hotel is not operational")
    if not trusted:
        raise BookingRejected("Hotel is not trusted based on reviews")
    if fully_booked:
        raise BookingRejected("Hotel is fully booked")


def calculate_price(user_status: str | None, promo_discount: float | None) -> tuple[float, float]:
    base = VIP_BASE_PRICE if (user_status or "").upper() == "VIP" else BASE_PRICE
    # как в монолите: скидка вычитается суммой, а не процентом
    discount = promo_discount or 0.0
    return discount, base - discount
