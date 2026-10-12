import pytest

from app.pricing import BookingRejected, calculate_price, check_hotel, check_user


def test_regular_user_without_promo_pays_base_price():
    assert calculate_price("ACTIVE", None) == (0.0, 100.0)


def test_vip_user_has_lower_base_price():
    assert calculate_price("VIP", None) == (0.0, 80.0)


def test_status_is_case_insensitive():
    assert calculate_price("vip", None) == (0.0, 80.0)


def test_unknown_user_status_gives_base_price():
    assert calculate_price(None, None) == (0.0, 100.0)


def test_promo_discount_is_subtracted_as_amount():
    assert calculate_price("VIP", 10.0) == (10.0, 70.0)
    assert calculate_price("ACTIVE", 10.0) == (10.0, 90.0)


@pytest.mark.parametrize(
    ("active", "blacklisted", "reason"),
    [(False, False, "inactive"), (True, True, "blacklisted")],
)
def test_user_checks_reject_booking(active, blacklisted, reason):
    with pytest.raises(BookingRejected, match=reason):
        check_user(active=active, blacklisted=blacklisted)


@pytest.mark.parametrize(
    ("operational", "trusted", "fully_booked", "reason"),
    [
        (False, True, False, "not operational"),
        (True, False, False, "not trusted"),
        (True, True, True, "fully booked"),
    ],
)
def test_hotel_checks_reject_booking(operational, trusted, fully_booked, reason):
    with pytest.raises(BookingRejected, match=reason):
        check_hotel(operational=operational, trusted=trusted, fully_booked=fully_booked)


def test_valid_user_and_hotel_pass_checks():
    check_user(active=True, blacklisted=False)
    check_hotel(operational=True, trusted=True, fully_booked=False)
