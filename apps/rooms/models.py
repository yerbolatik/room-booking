from __future__ import annotations

from decimal import Decimal

from django.core.validators import MinValueValidator
from django.db import models

from apps.core.models import TimestampedModel


class Room(TimestampedModel):
    """
    Represents a single bookable hotel room.

    Indexes:
        - price_per_night  — for price range filters and ordering
        - capacity         — for capacity filters and ordering
        - is_active        — for filtering available rooms
    """

    number = models.CharField(max_length=20, unique=True, verbose_name="Room number")
    name = models.CharField(max_length=100, verbose_name="Room name / title")
    description = models.TextField(blank=True, verbose_name="Description")
    price_per_night = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(Decimal("0.01"))],
        verbose_name="Price per night (USD)",
    )
    capacity = models.PositiveSmallIntegerField(
        validators=[MinValueValidator(1)],
        verbose_name="Capacity (number of beds)",
    )
    is_active = models.BooleanField(default=True, verbose_name="Is available for booking")

    class Meta:
        verbose_name = "Room"
        verbose_name_plural = "Rooms"
        ordering = ["number"]
        indexes = [
            models.Index(fields=["price_per_night"], name="room_price_idx"),
            models.Index(fields=["capacity"], name="room_capacity_idx"),
            models.Index(fields=["is_active"], name="room_active_idx"),
        ]

    def __str__(self) -> str:
        return f"Room {self.number} — {self.name}"
