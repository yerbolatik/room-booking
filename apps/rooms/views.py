from __future__ import annotations

from drf_spectacular.utils import OpenApiParameter, OpenApiTypes, extend_schema, extend_schema_view
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny
from rest_framework.request import Request
from rest_framework.response import Response

from .filters import RoomFilter
from .models import Room
from .serializers import RoomAvailabilityQuerySerializer, RoomSerializer
from .services import RoomAvailabilityService


@extend_schema(tags=["Rooms"])
@extend_schema_view(
    list=extend_schema(
        summary="List all active rooms",
        description=(
            "Returns a paginated list of hotel rooms. "
            "Supports filtering by price and capacity, and ordering."
        ),
    ),
    retrieve=extend_schema(summary="Retrieve room details"),
)
class RoomViewSet(viewsets.ReadOnlyModelViewSet):
    """
    Read-only viewset for Room resources.

    - **list**: paginated, filterable, orderable room catalogue
    - **retrieve**: single room detail
    - **available**: rooms without booking conflicts in a date window
    """

    serializer_class = RoomSerializer
    permission_classes = [AllowAny]
    filterset_class = RoomFilter
    search_fields = ["number", "name", "description"]
    ordering_fields = ["price_per_night", "capacity", "number"]
    ordering = ["number"]

    def get_queryset(self):  # type: ignore[override]
        return Room.objects.filter(is_active=True).order_by(*self.ordering)

    @extend_schema(
        summary="List available rooms in a date range",
        parameters=[
            OpenApiParameter(
                "check_in",
                OpenApiTypes.DATE,
                OpenApiParameter.QUERY,
                required=True,
                description="Check-in date (YYYY-MM-DD)",
            ),
            OpenApiParameter(
                "check_out",
                OpenApiTypes.DATE,
                OpenApiParameter.QUERY,
                required=True,
                description="Check-out date (YYYY-MM-DD)",
            ),
        ],
        responses={200: RoomSerializer(many=True)},
    )
    @action(detail=False, methods=["get"], url_path="available")
    def available(self, request: Request) -> Response:
        """Return rooms with no booking conflicts in the requested window."""
        query_serializer = RoomAvailabilityQuerySerializer(data=request.query_params)
        query_serializer.is_valid(raise_exception=True)

        check_in = query_serializer.validated_data["check_in"]
        check_out = query_serializer.validated_data["check_out"]

        base_qs = self.filter_queryset(self.get_queryset())
        available_rooms = RoomAvailabilityService.get_available_rooms(
            check_in=check_in,
            check_out=check_out,
            base_queryset=base_qs,
        )

        page = self.paginate_queryset(available_rooms)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(available_rooms, many=True)
        return Response(serializer.data)
