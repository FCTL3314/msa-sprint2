from urllib.parse import quote

import httpx


class MonolithUnavailable(Exception):
    pass


class MonolithClient:
    def __init__(self, base_url: str, timeout: float = 3.0):
        self._http = httpx.Client(base_url=base_url, timeout=timeout)

    def is_user_active(self, user_id: str) -> bool:
        return self._flag(f"/api/users/{quote(user_id)}/active")

    def is_user_blacklisted(self, user_id: str) -> bool:
        return self._flag(f"/api/users/{quote(user_id)}/blacklisted")

    def user_status(self, user_id: str) -> str | None:
        response = self._request("GET", f"/api/users/{quote(user_id)}/status")
        if response.status_code == 404:
            return None
        response.raise_for_status()
        return response.text

    def is_hotel_operational(self, hotel_id: str) -> bool:
        return self._flag(f"/api/hotels/{quote(hotel_id)}/operational")

    def is_hotel_trusted(self, hotel_id: str) -> bool:
        return self._flag(f"/api/reviews/hotel/{quote(hotel_id)}/trusted")

    def is_hotel_fully_booked(self, hotel_id: str) -> bool:
        return self._flag(f"/api/hotels/{quote(hotel_id)}/fully-booked")

    def promo_discount(self, code: str, user_id: str) -> float | None:
        # 400 - промокод не найден, истёк или не для этого пользователя
        response = self._request("POST", "/api/promos/validate", params={"code": code, "userId": user_id})
        if response.status_code == 400:
            return None
        response.raise_for_status()
        return float(response.json()["discount"])

    def _flag(self, path: str) -> bool:
        response = self._request("GET", path)
        response.raise_for_status()
        return response.json() is True

    def _request(self, method: str, path: str, **kwargs) -> httpx.Response:
        try:
            return self._http.request(method, path, **kwargs)
        except httpx.HTTPError as exc:
            raise MonolithUnavailable(f"Monolith is unavailable: {exc}") from exc
