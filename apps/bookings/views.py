from __future__ import annotations

from typing import Any

from django.db.models import QuerySet
from drf_spectacular.utils import OpenApiResponse, extend_schema, extend_schema_view
from rest_framework import filters, mixins, status, viewsets
from rest_framework.decorators import action
from rest_framework.generics import get_object_or_404
from rest_framework.permissions import BasePermission, IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.serializers import BaseSerializer

from .filters import BookingFilter
from .models import Booking
from .permissions import IsBookingOwnerOrAdmin
from .serializers import BookingCreateSerializer, BookingSerializer
from .services import BookingService


@extend_schema(tags=["Bookings"])
@extend_schema_view(
    list=extend_schema(summary="List my bookings"),
    retrieve=extend_schema(summary="Retrieve a booking"),
    create=extend_schema(
        summary="Create a booking",
        request=BookingCreateSerializer,
        responses={
            201: BookingSerializer,
            400: OpenApiResponse(description="Validation errors"),
            409: OpenApiResponse(description="Room not available"),
        },
    ),
)
class BookingViewSet(
    mixins.CreateModelMixin,
    mixins.RetrieveModelMixin,
    mixins.ListModelMixin,
    viewsets.GenericViewSet,  # type: ignore[type-arg]
):
    """
    Booking resource.

    - **list**     — authenticated user's own bookings (admin sees all)
    - **retrieve** — single booking (owner or admin only)
    - **create**   — book a room for a date range
    - **cancel**   — cancel an existing booking (owner or admin only)
    """

    permission_classes = [IsAuthenticated]
    filterset_class = BookingFilter
    filter_backends = [
        filters.OrderingFilter,
    ]
    ordering_fields = ["check_in", "check_out", "created_at", "total_price"]
    ordering = ["-created_at"]

    def get_queryset(self) -> QuerySet[Booking]:  # type: ignore[override]
        qs = (
            Booking.objects.select_related("room", "user")
            .order_by(*self.ordering)
        )
        # Non-staff users see only their own bookings.
        if not self.request.user.is_staff:
            qs = qs.filter(user=self.request.user)
        return qs

    def get_serializer_class(self) -> type[BaseSerializer[Any]]:  # type: ignore[override]
        if self.action == "create":
            return BookingCreateSerializer
        return BookingSerializer

    def get_permissions(self) -> list[BasePermission]:  # type: ignore[override]
        if self.action in ("retrieve", "cancel"):
            return [IsAuthenticated(), IsBookingOwnerOrAdmin()]
        return [IsAuthenticated()]

    def get_object(self) -> Booking:  # type: ignore[override]
        # Look up against the full table — not the user-scoped queryset — so
        # that IsBookingOwnerOrAdmin can issue a proper 403 instead of the
        # filtered queryset silently producing a 404 for other users' bookings.
        obj = get_object_or_404(
            Booking.objects.select_related("room", "user"),
            pk=self.kwargs["pk"],
        )
        self.check_object_permissions(self.request, obj)
        return obj

    # ------------------------------------------------------------------ #
    # create                                                             #
    # ------------------------------------------------------------------ #

    def create(self, request: Request, *args: object, **kwargs: object) -> Response:
        serializer = BookingCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        booking = BookingService.create_booking(
            user=request.user,
            room=serializer.validated_data["room"],
            check_in=serializer.validated_data["check_in"],
            check_out=serializer.validated_data["check_out"],
            notes=serializer.validated_data.get("notes", ""),
        )

        return Response(
            BookingSerializer(booking, context={"request": request}).data,
            status=status.HTTP_201_CREATED,
        )

    # ------------------------------------------------------------------ #
    # cancel                                                             #
    # ------------------------------------------------------------------ #

    @extend_schema(
        summary="Cancel a booking",
        request=None,
        responses={
            200: BookingSerializer,
            400: OpenApiResponse(description="Booking already cancelled"),
            403: OpenApiResponse(description="Not the booking owner"),
            404: OpenApiResponse(description="Booking not found"),
        },
    )
    @action(detail=True, methods=["post"], url_path="cancel")
    def cancel(self, request: Request, pk: str | None = None) -> Response:
        """Mark a booking as CANCELLED."""
        booking: Booking = self.get_object()  # applies IsBookingOwnerOrAdmin
        booking = BookingService.cancel_booking(booking=booking, user=request.user)
        return Response(
            BookingSerializer(booking, context={"request": request}).data,
            status=status.HTTP_200_OK,
        )
