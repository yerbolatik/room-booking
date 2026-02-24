from __future__ import annotations

from rest_framework import status
from rest_framework.exceptions import APIException


class RoomNotAvailableError(APIException):
    """Raised when the requested room is already booked for the given dates."""

    status_code = status.HTTP_409_CONFLICT
    default_detail = "The room is not available for the requested dates."
    default_code = "room_not_available"


class BookingCancellationError(APIException):
    """Raised when a booking cannot be cancelled (e.g., already cancelled)."""

    status_code = status.HTTP_400_BAD_REQUEST
    default_detail = "This booking cannot be cancelled."
    default_code = "booking_cancellation_error"
