from __future__ import annotations

from django.contrib import admin
from django.utils.html import format_html

from .models import Booking


@admin.register(Booking)
class BookingAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "user_email",
        "room_number",
        "check_in",
        "check_out",
        "nights_display",
        "total_price",
        "status_badge",
        "created_at",
    )
    list_filter = ("status", "check_in", "check_out", "room")
    search_fields = ("user__email", "room__number", "room__name")
    ordering = ("-created_at",)
    readonly_fields = (
        "user",
        "room",
        "check_in",
        "check_out",
        "total_price",
        "nights_display",
        "created_at",
        "updated_at",
    )
    autocomplete_fields: list[str] = []

    fieldsets = (
        ("Booking Details", {"fields": ("user", "room", "check_in", "check_out", "nights_display")}),
        ("Financials", {"fields": ("total_price",)}),
        ("Status & Notes", {"fields": ("status", "notes")}),
        ("Timestamps", {"fields": ("created_at", "updated_at"), "classes": ("collapse",)}),
    )

    @admin.display(description="Guest e-mail", ordering="user__email")
    def user_email(self, obj: Booking) -> str:
        return obj.user.email

    @admin.display(description="Room", ordering="room__number")
    def room_number(self, obj: Booking) -> str:
        return obj.room.number

    @admin.display(description="Nights")
    def nights_display(self, obj: Booking) -> int | str:
        if not obj.check_in or not obj.check_out:
            return "—"
        return obj.nights

    @admin.display(description="Status")
    def status_badge(self, obj: Booking) -> str:
        colour = "#28a745" if obj.status == Booking.Status.CONFIRMED else "#dc3545"
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>',
            colour,
            obj.get_status_display(),
        )
