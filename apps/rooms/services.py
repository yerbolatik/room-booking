"""
Room domain services.

Business logic lives here, NOT in views or models, following the
service-layer pattern for clean separation of concerns.
"""
from __future__ import annotations

import datetime

from django.db.models import QuerySet

from .models import Room


class RoomAvailabilityService:
    """Encapsulates room-availability query logic."""

    @staticmethod
    def get_available_rooms(
        check_in: datetime.date,
        check_out: datetime.date,
        base_queryset: QuerySet[Room] | None = None,
    ) -> QuerySet[Room]:
        """
        Return active rooms that have no confirmed booking overlapping
        the requested [check_in, check_out) window.

        Overlap condition (Allen's interval algebra — any of):
            existing.check_in  < requested.check_out
            AND
            existing.check_out > requested.check_in

        Rooms with a CANCELLED booking for the same window are still
        considered available.
        """
        from apps.bookings.models import Booking  # avoid circular import

        qs = base_queryset if base_queryset is not None else Room.objects.all()
        qs = qs.filter(is_active=True)

        overlapping_room_ids = (
            Booking.objects.filter(
                status=Booking.Status.CONFIRMED,
                check_in__lt=check_out,
                check_out__gt=check_in,
            )
            .values_list("room_id", flat=True)
            .distinct()
        )

        return qs.exclude(id__in=overlapping_room_ids)
