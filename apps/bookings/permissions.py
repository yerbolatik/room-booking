from __future__ import annotations

from rest_framework.permissions import BasePermission
from rest_framework.request import Request
from rest_framework.views import APIView

from .models import Booking


class IsBookingOwnerOrAdmin(BasePermission):
    """
    Object-level permission:
        - Staff / superusers have unrestricted access.
        - Regular users may only access bookings they own.
    """

    message = "You do not have permission to access this booking."

    def has_object_permission(self, request: Request, view: APIView, obj: Booking) -> bool:
        if request.user and request.user.is_staff:
            return True
        return obj.user_id == request.user.pk
