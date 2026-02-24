from __future__ import annotations

from rest_framework import serializers

from .models import Room


class RoomSerializer(serializers.ModelSerializer):
    """Full room representation — used for list and detail endpoints."""

    class Meta:
        model = Room
        fields = [
            "id",
            "number",
            "name",
            "description",
            "price_per_night",
            "capacity",
            "is_active",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]


class RoomAvailabilityQuerySerializer(serializers.Serializer):
    """
    Query-parameter schema for the availability search endpoint.

    Used only for OpenAPI documentation and input validation.
    """

    check_in = serializers.DateField(
        required=True,
        help_text="Desired check-in date (YYYY-MM-DD).",
    )
    check_out = serializers.DateField(
        required=True,
        help_text="Desired check-out date (YYYY-MM-DD).",
    )

    def validate(self, attrs: dict) -> dict:
        if attrs["check_in"] >= attrs["check_out"]:
            raise serializers.ValidationError("check_out must be after check_in.")
        return attrs
