from __future__ import annotations

from rest_framework.routers import DefaultRouter

from .views import RoomViewSet

app_name = "rooms"

router = DefaultRouter()
router.register(r"", RoomViewSet, basename="room")

urlpatterns = router.urls
