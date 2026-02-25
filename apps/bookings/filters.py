from __future__ import annotations

import django_filters

from .models import Booking


class BookingFilter(django_filters.FilterSet):  # type: ignore[misc]
    """
    Filtering options for the Booking list endpoint.

    Non-staff users only ever see their own bookings (enforced in the view),
    but staff users can use these filters across all bookings.
    """

    status = django_filters.ChoiceFilter(choices=Booking.Status.choices)
    check_in_after = django_filters.DateFilter(field_name="check_in", lookup_expr="gte")
    check_in_before = django_filters.DateFilter(field_name="check_in", lookup_expr="lte")
    check_out_after = django_filters.DateFilter(field_name="check_out", lookup_expr="gte")
    check_out_before = django_filters.DateFilter(field_name="check_out", lookup_expr="lte")
    room_id = django_filters.NumberFilter(field_name="room__id")

    class Meta:
        model = Booking
        fields = [
            "status",
            "check_in_after",
            "check_in_before",
            "check_out_after",
            "check_out_before",
            "room_id",
        ]
