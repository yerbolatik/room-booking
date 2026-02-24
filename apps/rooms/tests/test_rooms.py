"""
Tests for the Room catalogue and availability search.

Rooms are publicly accessible — no authentication is required for any
read endpoint in this suite.
"""
from __future__ import annotations

import datetime
from decimal import Decimal

import pytest
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

from apps.rooms.models import Room


# ─────────────────────────────────────────────────────────────────────────────
# Shared fixtures
# ─────────────────────────────────────────────────────────────────────────────


@pytest.fixture()
def client() -> APIClient:
    """Unauthenticated client — rooms are public."""
    return APIClient()


@pytest.fixture()
def room_a(db) -> Room:
    return Room.objects.create(
        number="101",
        name="Single Standard",
        price_per_night=Decimal("80.00"),
        capacity=1,
        is_active=True,
    )


@pytest.fixture()
def room_b(db) -> Room:
    return Room.objects.create(
        number="201",
        name="Double Deluxe",
        price_per_night=Decimal("160.00"),
        capacity=2,
        is_active=True,
    )


@pytest.fixture()
def inactive_room(db) -> Room:
    return Room.objects.create(
        number="999",
        name="Maintenance",
        price_per_night=Decimal("50.00"),
        capacity=1,
        is_active=False,
    )


# ─────────────────────────────────────────────────────────────────────────────
# Room list — publicly accessible
# ─────────────────────────────────────────────────────────────────────────────


@pytest.mark.django_db
class TestRoomList:
    url = "/api/v1/rooms/"

    def test_anyone_can_list_rooms(self, client: APIClient, room_a: Room) -> None:
        """No auth credentials -> 200 OK."""
        response = client.get(self.url)
        assert response.status_code == status.HTTP_200_OK

    def test_inactive_rooms_excluded(
        self, client: APIClient, room_a: Room, inactive_room: Room
    ) -> None:
        response = client.get(self.url)
        numbers = [r["number"] for r in response.json()["results"]]
        assert room_a.number in numbers
        assert inactive_room.number not in numbers

    def test_filter_price_min(
        self, client: APIClient, room_a: Room, room_b: Room
    ) -> None:
        response = client.get(self.url, {"price_min": "100"})
        numbers = [r["number"] for r in response.json()["results"]]
        assert room_b.number in numbers
        assert room_a.number not in numbers

    def test_filter_price_max(
        self, client: APIClient, room_a: Room, room_b: Room
    ) -> None:
        response = client.get(self.url, {"price_max": "100"})
        numbers = [r["number"] for r in response.json()["results"]]
        assert room_a.number in numbers
        assert room_b.number not in numbers

    def test_filter_capacity_min(
        self, client: APIClient, room_a: Room, room_b: Room
    ) -> None:
        response = client.get(self.url, {"capacity_min": "2"})
        numbers = [r["number"] for r in response.json()["results"]]
        assert room_b.number in numbers
        assert room_a.number not in numbers

    def test_order_by_price_ascending(
        self, client: APIClient, room_a: Room, room_b: Room
    ) -> None:
        response = client.get(self.url, {"ordering": "price_per_night"})
        prices = [Decimal(r["price_per_night"]) for r in response.json()["results"]]
        assert prices == sorted(prices)

    def test_order_by_price_descending(
        self, client: APIClient, room_a: Room, room_b: Room
    ) -> None:
        response = client.get(self.url, {"ordering": "-price_per_night"})
        prices = [Decimal(r["price_per_night"]) for r in response.json()["results"]]
        assert prices == sorted(prices, reverse=True)


# ─────────────────────────────────────────────────────────────────────────────
# Room detail — publicly accessible
# ─────────────────────────────────────────────────────────────────────────────


@pytest.mark.django_db
class TestRoomDetail:
    def test_anyone_can_view_room_detail(self, client: APIClient, room_a: Room) -> None:
        url = reverse("rooms:room-detail", kwargs={"pk": room_a.pk})
        response = client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert response.json()["number"] == room_a.number

    def test_nonexistent_room_returns_404(self, client: APIClient, db) -> None:
        url = reverse("rooms:room-detail", kwargs={"pk": 99999})
        response = client.get(url)
        assert response.status_code == status.HTTP_404_NOT_FOUND


# ─────────────────────────────────────────────────────────────────────────────
# Availability search — publicly accessible
# ─────────────────────────────────────────────────────────────────────────────


@pytest.fixture()
def today() -> datetime.date:
    return datetime.date.today()


@pytest.mark.django_db
class TestRoomAvailability:
    url = "/api/v1/rooms/available/"

    def test_anyone_can_search_availability(
        self, client: APIClient, room_a: Room, today: datetime.date
    ) -> None:
        """No auth required for availability search."""
        params = {
            "check_in": str(today),
            "check_out": str(today + datetime.timedelta(days=2)),
        }
        response = client.get(self.url, params)
        assert response.status_code == status.HTTP_200_OK

    def test_free_rooms_appear_in_results(
        self, client: APIClient, room_a: Room, room_b: Room, today: datetime.date
    ) -> None:
        params = {
            "check_in": str(today),
            "check_out": str(today + datetime.timedelta(days=2)),
        }
        response = client.get(self.url, params)
        numbers = [r["number"] for r in response.json()["results"]]
        assert room_a.number in numbers
        assert room_b.number in numbers

    def test_confirmed_booked_room_excluded(
        self,
        client: APIClient,
        room_a: Room,
        room_b: Room,
        today: datetime.date,
        django_user_model,
    ) -> None:
        from apps.bookings.models import Booking

        user = django_user_model.objects.create_user(
            email="guest@example.com", username="Guest", password="pass"
        )
        Booking.objects.create(
            user=user,
            room=room_a,
            check_in=today,
            check_out=today + datetime.timedelta(days=3),
            status=Booking.Status.CONFIRMED,
            total_price=Decimal("240.00"),
        )

        params = {
            "check_in": str(today + datetime.timedelta(days=1)),
            "check_out": str(today + datetime.timedelta(days=2)),
        }
        response = client.get(self.url, params)
        numbers = [r["number"] for r in response.json()["results"]]
        assert room_a.number not in numbers  # booked — excluded
        assert room_b.number in numbers      # free — included

    def test_cancelled_booking_does_not_block_room(
        self,
        client: APIClient,
        room_a: Room,
        today: datetime.date,
        django_user_model,
    ) -> None:
        from apps.bookings.models import Booking

        user = django_user_model.objects.create_user(
            email="guest2@example.com", username="Guest2", password="pass"
        )
        Booking.objects.create(
            user=user,
            room=room_a,
            check_in=today,
            check_out=today + datetime.timedelta(days=3),
            status=Booking.Status.CANCELLED,
            total_price=Decimal("240.00"),
        )

        params = {
            "check_in": str(today),
            "check_out": str(today + datetime.timedelta(days=3)),
        }
        response = client.get(self.url, params)
        numbers = [r["number"] for r in response.json()["results"]]
        assert room_a.number in numbers  # cancelled -> room is still free

    def test_missing_check_in_returns_400(self, client: APIClient, db) -> None:
        response = client.get(self.url, {"check_out": "2030-01-10"})
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_check_in_equals_check_out_returns_400(self, client: APIClient, db) -> None:
        response = client.get(
            self.url, {"check_in": "2030-06-01", "check_out": "2030-06-01"}
        )
        assert response.status_code == status.HTTP_400_BAD_REQUEST
