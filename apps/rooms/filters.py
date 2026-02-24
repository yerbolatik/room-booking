from __future__ import annotations

import django_filters

from .models import Room


class RoomFilter(django_filters.FilterSet):
    """
    Filtering options for the Room list endpoint.

    Supported query parameters:
        price_min           — rooms with price_per_night >= value
        price_max           — rooms with price_per_night <= value
        capacity_min        — rooms with capacity >= value
        capacity_max        — rooms with capacity <= value
        is_active           — filter by active status (true/false)
        check_in / check_out — availability window (handled by the view/service layer)
    """

    price_min = django_filters.NumberFilter(
        field_name="price_per_night",
        lookup_expr="gte",
        label="Minimum price per night",
    )
    price_max = django_filters.NumberFilter(
        field_name="price_per_night",
        lookup_expr="lte",
        label="Maximum price per night",
    )
    capacity_min = django_filters.NumberFilter(
        field_name="capacity",
        lookup_expr="gte",
        label="Minimum capacity (beds)",
    )
    capacity_max = django_filters.NumberFilter(
        field_name="capacity",
        lookup_expr="lte",
        label="Maximum capacity (beds)",
    )
    class Meta:
        model = Room
        fields = [
            "price_min",
            "price_max",
            "capacity_min",
            "capacity_max",
            "is_active",
        ]
