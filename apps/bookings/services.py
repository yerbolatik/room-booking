"""
Booking domain service.

All business logic for creating and cancelling bookings lives here.
Views are kept thin — they delegate to this service exclusively.
"""
from __future__ import annotations

import datetime
import logging
from decimal import Decimal

from django.db import transaction

from apps.rooms.models import Room

from .exceptions import BookingCancellationError, RoomNotAvailableError
from .models import Booking

logger = logging.getLogger(__name__)


class BookingService:
    """
    Stateless service — every method is a @staticmethod so callers never
    need to instantiate this class.
    """

    # ------------------------------------------------------------------ #
    # Public API                                                         #
    # ------------------------------------------------------------------ #

    @staticmethod
    def create_booking(
        *,
        user,
        room: Room,
        check_in: datetime.date,
        check_out: datetime.date,
        notes: str = "",
    ) -> Booking:
        """
        Create a confirmed booking for *room* over [check_in, check_out).

        Algorithm (inside a serialisable transaction):
            1. Lock the room row with SELECT FOR UPDATE to prevent races.
            2. Verify the room is active.
            3. Check for any CONFIRMED booking that overlaps the window.
            4. Calculate total price.
            5. Persist and return the new Booking.

        Raises:
            RoomNotAvailableError — room inactive or dates overlap an
                                    existing confirmed booking.
        """
        if check_in >= check_out:
            raise ValueError("check_out must be strictly after check_in.")

        with transaction.atomic():
            # Step 1 - row-level lock on the room.
            try:
                room = Room.objects.select_for_update().get(pk=room.pk)
            except Room.DoesNotExist:
                raise RoomNotAvailableError("Room does not exist.")

            # Step 2 - room must be active.
            if not room.is_active:
                raise RoomNotAvailableError("Room is not available for booking.")

            # Step 3 — overlap check.
            conflict = BookingService._has_conflict(room, check_in, check_out)
            if conflict:
                raise RoomNotAvailableError(
                    f"Room {room.number!r} is already booked for the requested period."
                )

            # Step 4 — calculate price.
            nights: int = (check_out - check_in).days
            total_price: Decimal = room.price_per_night * nights

            # Step 5 — persist.
            booking = Booking.objects.create(
                user=user,
                room=room,
                check_in=check_in,
                check_out=check_out,
                status=Booking.Status.CONFIRMED,
                total_price=total_price,
                notes=notes,
            )

        logger.info(
            "Booking #%s created: user=%s room=%s %s->%s",
            booking.pk,
            user.pk,
            room.pk,
            check_in,
            check_out,
        )
        return booking

    @staticmethod
    def cancel_booking(*, booking: Booking, user) -> Booking:
        """
        Cancel a booking owned by *user*.

        Only the owning user (or an admin) may cancel.
        A booking that is already CANCELLED cannot be cancelled again.

        Raises:
            BookingCancellationError — already cancelled, or user mismatch.
        """
        if booking.status == Booking.Status.CANCELLED:
            raise BookingCancellationError("Booking is already cancelled.")

        if booking.user_id != user.pk and not user.is_staff:
            raise BookingCancellationError("You do not own this booking.")

        with transaction.atomic():
            booking.status = Booking.Status.CANCELLED
            booking.save(update_fields=["status", "updated_at"])

        logger.info("Booking #%s cancelled by user=%s", booking.pk, user.pk)
        return booking

    # ------------------------------------------------------------------ #
    # Private helpers                                                    #
    # ------------------------------------------------------------------ #

    @staticmethod
    def _has_conflict(
        room: Room,
        check_in: datetime.date,
        check_out: datetime.date,
    ) -> bool:
        """
        Return True if any CONFIRMED booking for *room* overlaps [check_in, check_out).

        Two intervals [a, b) and [c, d) overlap when:
            a < d  AND  b > c
        """
        return Booking.objects.filter(
            room=room,
            status=Booking.Status.CONFIRMED,
            check_in__lt=check_out,
            check_out__gt=check_in,
        ).exists()
