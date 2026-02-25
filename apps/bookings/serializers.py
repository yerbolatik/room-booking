from __future__ import annotations

import datetime
from typing import Any

from rest_framework import serializers

from apps.rooms.models import Room
from apps.rooms.serializers import RoomSerializer

from .models import Booking


class BookingCreateSerializer(serializers.Serializer[dict[str, Any]]):
    """Input serializer for booking creation — validates dates only."""

    room_id = serializers.PrimaryKeyRelatedField(
        queryset=Room.objects.filter(is_active=True),
        source="room",
        help_text="ID of the room to book.",
    )
    check_in = serializers.DateField(help_text="Check-in date (YYYY-MM-DD).")
    check_out = serializers.DateField(help_text="Check-out date (YYYY-MM-DD).")
    notes = serializers.CharField(
        required=False,
        allow_blank=True,
        default="",
        max_length=1000,
        help_text="Optional guest notes.",
    )

    def validate(self, attrs: dict[str, Any]) -> dict[str, Any]:
        today = datetime.date.today()

        if attrs["check_in"] < today:
            raise serializers.ValidationError({"check_in": "Check-in cannot be in the past."})

        if attrs["check_in"] >= attrs["check_out"]:
            raise serializers.ValidationError(
                {"check_out": "check_out must be after check_in."}
            )

        return attrs


class BookingSerializer(serializers.ModelSerializer[Booking]):
    """Full booking representation returned to clients."""

    room = RoomSerializer(read_only=True)
    user_id = serializers.IntegerField(source="user.id", read_only=True)
    user_email = serializers.EmailField(source="user.email", read_only=True)
    nights = serializers.IntegerField(read_only=True)

    class Meta:
        model = Booking
        fields = [
            "id",
            "user_id",
            "user_email",
            "room",
            "check_in",
            "check_out",
            "nights",
            "status",
            "total_price",
            "notes",
            "created_at",
            "updated_at",
        ]
        read_only_fields = fields
