from __future__ import annotations

import logging
from typing import Any

from django.core.exceptions import PermissionDenied, ValidationError
from django.http import Http404
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import exception_handler

logger = logging.getLogger(__name__)


def custom_exception_handler(exc: Exception, context: dict[str, Any]) -> Response | None:
    """
    Custom DRF exception handler that normalises error responses to:

        {
            "error": "<human-readable message>",
            "detail": <original DRF detail or list>   # optional
        }

    and maps a few Django core exceptions to proper HTTP statuses.
    """
    # Let DRF handle its own exceptions first.
    response = exception_handler(exc, context)

    if response is not None:
        data = response.data
        # Flatten single-key "detail" responses.
        if isinstance(data, dict) and list(data.keys()) == ["detail"]:
            response.data = {"error": str(data["detail"])}
        elif isinstance(data, dict | list):
            response.data = {"errors": data}
        return response

    # Handle Django-native exceptions not caught by DRF.
    if isinstance(exc, Http404):
        return Response(
            {"error": "Not found."},
            status=status.HTTP_404_NOT_FOUND,
        )

    if isinstance(exc, PermissionDenied):
        return Response(
            {"error": "Permission denied."},
            status=status.HTTP_403_FORBIDDEN,
        )

    if isinstance(exc, ValidationError):
        return Response(
            {"errors": exc.message_dict if hasattr(exc, "message_dict") else exc.messages},
            status=status.HTTP_400_BAD_REQUEST,
        )

    # Unhandled — let Django's 500 machinery deal with it.
    logger.exception("Unhandled exception", exc_info=exc)
    return None
