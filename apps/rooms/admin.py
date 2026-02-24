from __future__ import annotations

from django.contrib import admin

from .models import Room


@admin.register(Room)
class RoomAdmin(admin.ModelAdmin):
    list_display = (
        "number",
        "name",
        "price_per_night",
        "capacity",
        "is_active",
        "created_at",
    )
    list_filter = ("is_active",)
    search_fields = ("number", "name", "description")
    list_editable = ("is_active",)
    ordering = ("number",)
    readonly_fields = ("created_at", "updated_at")

    fieldsets = (
        (
            "Room Identity",
            {"fields": ("number", "name", "description")},
        ),
        (
            "Pricing & Capacity",
            {"fields": ("price_per_night", "capacity")},
        ),
        (
            "Status",
            {"fields": ("is_active",)},
        ),
        (
            "Timestamps",
            {"fields": ("created_at", "updated_at"), "classes": ("collapse",)},
        ),
    )
