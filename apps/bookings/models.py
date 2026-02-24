from __future__ import annotations

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models

from apps.core.models import TimestampedModel


class Booking(TimestampedModel):
    """
    Represents a room reservation made by an authenticated user.

    Overlap prevention strategy (defence-in-depth):
        1. Application level — BookingService.create_booking raises a
           RoomNotAvailableError before any INSERT when it detects a
           conflict using select_for_update() inside a transaction.
        2. Database level — a CheckConstraint enforces check_out > check_in
           at the storage layer, preventing nonsensical date ranges.

    Indexes:
        - (room, check_in, check_out) — overlap query
        - (user, status)              — "my bookings" list query
        - check_in / check_out        — availability range scans
    """

    class Status(models.TextChoices):
        CONFIRMED = "CONFIRMED", "Confirmed"
        CANCELLED = "CANCELLED", "Cancelled"

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="bookings",
        verbose_name="Guest",
    )
    room = models.ForeignKey(
        "rooms.Room",
        on_delete=models.PROTECT,
        related_name="bookings",
        verbose_name="Room",
    )
    check_in = models.DateField(verbose_name="Check-in date")
    check_out = models.DateField(verbose_name="Check-out date")
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.CONFIRMED,
        db_index=True,
    )
    total_price = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        verbose_name="Total price (USD)",
    )
    notes = models.TextField(blank=True, verbose_name="Guest notes")

    class Meta:
        verbose_name = "Booking"
        verbose_name_plural = "Bookings"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["room", "check_in", "check_out"], name="booking_room_dates_idx"),
            models.Index(fields=["user", "status"], name="booking_user_status_idx"),
            models.Index(fields=["check_in"], name="booking_check_in_idx"),
            models.Index(fields=["check_out"], name="booking_check_out_idx"),
        ]
        constraints = [
            models.CheckConstraint(
                check=models.Q(check_out__gt=models.F("check_in")),
                name="booking_checkout_after_checkin",
            ),
        ]

    def __str__(self) -> str:
        return (
            f"Booking #{self.pk} — Room {self.room_id} "
            f"({self.check_in} -> {self.check_out}) [{self.status}]"
        )

    @property
    def nights(self) -> int:
        return (self.check_out - self.check_in).days

    def clean(self) -> None:
        if self.check_in and self.check_out and self.check_in >= self.check_out:
            raise ValidationError(
                {"check_out": "Check-out date must be after check-in date."}
            )
