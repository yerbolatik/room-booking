"""
Tests for booking creation, cancellation, and overlap prevention.
"""
from __future__ import annotations

import datetime
from decimal import Decimal

import pytest
from rest_framework import status
from rest_framework.test import APIClient

from apps.bookings.models import Booking
from apps.bookings.services import BookingService
from apps.rooms.models import Room

# ─────────────────────────────────────────────────────────────────────────────
# Fixtures
# ─────────────────────────────────────────────────────────────────────────────


@pytest.fixture()
def today() -> datetime.date:
    return datetime.date.today()


@pytest.fixture()
def room(db) -> Room:
    return Room.objects.create(
        number="101",
        name="Standard Room",
        price_per_night=Decimal("100.00"),
        capacity=2,
        is_active=True,
    )


@pytest.fixture()
def second_room(db) -> Room:
    return Room.objects.create(
        number="202",
        name="Deluxe Suite",
        price_per_night=Decimal("250.00"),
        capacity=4,
        is_active=True,
    )


@pytest.fixture()
def user(db, django_user_model):
    return django_user_model.objects.create_user(
        email="alice@example.com",
        username="Alice Smith",
        first_name="Alice",
        last_name="Smith",
        password="StrongP@ss123",
    )


@pytest.fixture()
def another_user(db, django_user_model):
    return django_user_model.objects.create_user(
        email="bob@example.com",
        username="Bob Jones",
        first_name="Bob",
        last_name="Jones",
        password="StrongP@ss123",
    )


@pytest.fixture()
def auth_client(user) -> APIClient:
    client = APIClient()
    client.force_authenticate(user=user)
    return client


@pytest.fixture()
def another_auth_client(another_user) -> APIClient:
    client = APIClient()
    client.force_authenticate(user=another_user)
    return client


@pytest.fixture()
def anon_client() -> APIClient:
    return APIClient()


# ─────────────────────────────────────────────────────────────────────────────
# Unit tests — BookingService
# ─────────────────────────────────────────────────────────────────────────────


@pytest.mark.django_db
class TestBookingServiceCreateBooking:
    def test_creates_confirmed_booking(
        self, user, room: Room, today: datetime.date
    ) -> None:
        booking = BookingService.create_booking(
            user=user,
            room=room,
            check_in=today,
            check_out=today + datetime.timedelta(days=3),
        )

        assert booking.pk is not None
        assert booking.status == Booking.Status.CONFIRMED
        assert booking.total_price == Decimal("300.00")  # 3 nights × 100

    def test_calculates_total_price_correctly(
        self, user, room: Room, today: datetime.date
    ) -> None:
        nights = 5
        booking = BookingService.create_booking(
            user=user,
            room=room,
            check_in=today,
            check_out=today + datetime.timedelta(days=nights),
        )
        assert booking.total_price == room.price_per_night * nights

    def test_raises_on_overlapping_booking(
        self, user, room: Room, today: datetime.date
    ) -> None:
        from apps.bookings.exceptions import RoomNotAvailableError

        BookingService.create_booking(
            user=user,
            room=room,
            check_in=today,
            check_out=today + datetime.timedelta(days=5),
        )

        with pytest.raises(RoomNotAvailableError):
            BookingService.create_booking(
                user=user,
                room=room,
                check_in=today + datetime.timedelta(days=2),
                check_out=today + datetime.timedelta(days=7),
            )

    def test_adjacent_bookings_do_not_conflict(
        self, user, room: Room, today: datetime.date
    ) -> None:
        """[0,3) and [3,6) are adjacent — must NOT conflict."""
        check_out_first = today + datetime.timedelta(days=3)
        BookingService.create_booking(
            user=user,
            room=room,
            check_in=today,
            check_out=check_out_first,
        )
        booking2 = BookingService.create_booking(
            user=user,
            room=room,
            check_in=check_out_first,
            check_out=check_out_first + datetime.timedelta(days=3),
        )
        assert booking2.pk is not None

    def test_cancelled_booking_does_not_block_new_booking(
        self, user, room: Room, today: datetime.date
    ) -> None:
        booking = BookingService.create_booking(
            user=user,
            room=room,
            check_in=today,
            check_out=today + datetime.timedelta(days=3),
        )
        BookingService.cancel_booking(booking=booking, user=user)

        # Same dates — should succeed after cancellation.
        new_booking = BookingService.create_booking(
            user=user,
            room=room,
            check_in=today,
            check_out=today + datetime.timedelta(days=3),
        )
        assert new_booking.pk is not None

    def test_raises_for_inactive_room(
        self, user, room: Room, today: datetime.date
    ) -> None:
        from apps.bookings.exceptions import RoomNotAvailableError

        room.is_active = False
        room.save()

        with pytest.raises(RoomNotAvailableError):
            BookingService.create_booking(
                user=user,
                room=room,
                check_in=today,
                check_out=today + datetime.timedelta(days=2),
            )

    def test_raises_for_invalid_date_order(
        self, user, room: Room, today: datetime.date
    ) -> None:
        with pytest.raises(ValueError):
            BookingService.create_booking(
                user=user,
                room=room,
                check_in=today + datetime.timedelta(days=3),
                check_out=today,
            )


@pytest.mark.django_db
class TestBookingServiceCancelBooking:
    def test_owner_can_cancel_booking(
        self, user, room: Room, today: datetime.date
    ) -> None:
        booking = BookingService.create_booking(
            user=user,
            room=room,
            check_in=today,
            check_out=today + datetime.timedelta(days=2),
        )
        cancelled = BookingService.cancel_booking(booking=booking, user=user)
        assert cancelled.status == Booking.Status.CANCELLED

    def test_cannot_cancel_already_cancelled_booking(
        self, user, room: Room, today: datetime.date
    ) -> None:
        from apps.bookings.exceptions import BookingCancellationError

        booking = BookingService.create_booking(
            user=user,
            room=room,
            check_in=today,
            check_out=today + datetime.timedelta(days=2),
        )
        BookingService.cancel_booking(booking=booking, user=user)

        with pytest.raises(BookingCancellationError):
            BookingService.cancel_booking(booking=booking, user=user)

    def test_other_user_cannot_cancel_booking(
        self, user, another_user, room: Room, today: datetime.date
    ) -> None:
        from apps.bookings.exceptions import BookingCancellationError

        booking = BookingService.create_booking(
            user=user,
            room=room,
            check_in=today,
            check_out=today + datetime.timedelta(days=2),
        )

        with pytest.raises(BookingCancellationError):
            BookingService.cancel_booking(booking=booking, user=another_user)


# ─────────────────────────────────────────────────────────────────────────────
# API tests — Booking endpoints
# ─────────────────────────────────────────────────────────────────────────────


@pytest.mark.django_db
class TestBookingAPICreate:
    url = "/api/v1/bookings/"

    def test_unauthenticated_user_cannot_book(
        self, anon_client: APIClient, room: Room, today: datetime.date
    ) -> None:
        payload = {
            "room_id": room.pk,
            "check_in": str(today),
            "check_out": str(today + datetime.timedelta(days=2)),
        }
        response = anon_client.post(self.url, payload, format="json")
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_authenticated_user_can_book(
        self, auth_client: APIClient, room: Room, today: datetime.date
    ) -> None:
        payload = {
            "room_id": room.pk,
            "check_in": str(today),
            "check_out": str(today + datetime.timedelta(days=3)),
        }
        response = auth_client.post(self.url, payload, format="json")

        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        assert data["status"] == Booking.Status.CONFIRMED
        assert Decimal(data["total_price"]) == Decimal("300.00")

    def test_booking_conflict_returns_409(
        self, auth_client: APIClient, room: Room, today: datetime.date
    ) -> None:
        payload = {
            "room_id": room.pk,
            "check_in": str(today),
            "check_out": str(today + datetime.timedelta(days=5)),
        }
        auth_client.post(self.url, payload, format="json")

        # Second booking overlaps with the first.
        response = auth_client.post(
            self.url,
            {
                "room_id": room.pk,
                "check_in": str(today + datetime.timedelta(days=2)),
                "check_out": str(today + datetime.timedelta(days=7)),
            },
            format="json",
        )
        assert response.status_code == status.HTTP_409_CONFLICT

    def test_past_check_in_returns_400(
        self, auth_client: APIClient, room: Room, today: datetime.date
    ) -> None:
        payload = {
            "room_id": room.pk,
            "check_in": str(today - datetime.timedelta(days=1)),
            "check_out": str(today + datetime.timedelta(days=1)),
        }
        response = auth_client.post(self.url, payload, format="json")
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_check_in_equal_check_out_returns_400(
        self, auth_client: APIClient, room: Room, today: datetime.date
    ) -> None:
        payload = {
            "room_id": room.pk,
            "check_in": str(today),
            "check_out": str(today),
        }
        response = auth_client.post(self.url, payload, format="json")
        assert response.status_code == status.HTTP_400_BAD_REQUEST


@pytest.mark.django_db
class TestBookingAPIList:
    url = "/api/v1/bookings/"

    def test_user_sees_only_own_bookings(
        self,
        auth_client: APIClient,
        another_auth_client: APIClient,
        room: Room,
        second_room: Room,
        user,
        another_user,
        today: datetime.date,
    ) -> None:
        BookingService.create_booking(
            user=user,
            room=room,
            check_in=today,
            check_out=today + datetime.timedelta(days=2),
        )
        BookingService.create_booking(
            user=another_user,
            room=second_room,
            check_in=today,
            check_out=today + datetime.timedelta(days=2),
        )

        response = auth_client.get(self.url)
        assert response.status_code == status.HTTP_200_OK
        for booking in response.json()["results"]:
            assert booking["user_id"] == user.pk

    def test_unauthenticated_cannot_list_bookings(
        self, anon_client: APIClient
    ) -> None:
        response = anon_client.get(self.url)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED


@pytest.mark.django_db
class TestBookingAPICancel:
    def test_owner_can_cancel_via_api(
        self, auth_client: APIClient, user, room: Room, today: datetime.date
    ) -> None:
        booking = BookingService.create_booking(
            user=user,
            room=room,
            check_in=today,
            check_out=today + datetime.timedelta(days=2),
        )
        url = f"/api/v1/bookings/{booking.pk}/cancel/"
        response = auth_client.post(url)

        assert response.status_code == status.HTTP_200_OK
        assert response.json()["status"] == Booking.Status.CANCELLED

    def test_other_user_cannot_cancel_booking(
        self,
        auth_client: APIClient,
        another_auth_client: APIClient,
        user,
        room: Room,
        today: datetime.date,
    ) -> None:
        booking = BookingService.create_booking(
            user=user,
            room=room,
            check_in=today,
            check_out=today + datetime.timedelta(days=2),
        )
        url = f"/api/v1/bookings/{booking.pk}/cancel/"
        response = another_auth_client.post(url)

        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_unauthenticated_cannot_cancel(
        self, anon_client: APIClient, user, room: Room, today: datetime.date
    ) -> None:
        booking = BookingService.create_booking(
            user=user,
            room=room,
            check_in=today,
            check_out=today + datetime.timedelta(days=2),
        )
        url = f"/api/v1/bookings/{booking.pk}/cancel/"
        response = anon_client.post(url)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_staff_can_cancel_any_booking(
        self, user, room: Room, today: datetime.date, django_user_model
    ) -> None:
        """Staff user can cancel a booking that belongs to another user."""
        booking = BookingService.create_booking(
            user=user,
            room=room,
            check_in=today,
            check_out=today + datetime.timedelta(days=2),
        )
        staff = django_user_model.objects.create_user(
            email="staff@example.com",
            username="Staff",
            password="StrongP@ss123",
            is_staff=True,
        )
        staff_client = APIClient()
        staff_client.force_authenticate(user=staff)

        url = f"/api/v1/bookings/{booking.pk}/cancel/"
        response = staff_client.post(url)

        assert response.status_code == status.HTTP_200_OK
        assert response.json()["status"] == Booking.Status.CANCELLED
