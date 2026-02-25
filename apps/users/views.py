from __future__ import annotations

from typing import Any

from django.contrib.auth import get_user_model
from drf_spectacular.utils import OpenApiResponse, extend_schema, extend_schema_view
from rest_framework import generics, status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

from .serializers import (
    CustomTokenObtainPairSerializer,
    UserProfileSerializer,
    UserRegistrationSerializer,
)

User = get_user_model()


@extend_schema(tags=["Auth"])
@extend_schema_view(
    post=extend_schema(
        summary="Register a new user",
        auth=[],
        responses={
            201: UserProfileSerializer,
            400: OpenApiResponse(description="Validation errors"),
        },
    )
)
class RegisterView(generics.CreateAPIView):  # type: ignore[type-arg]
    """
    Register a new user account.

    Returns the created user profile (without password fields).
    """

    queryset = User.objects.none()
    serializer_class = UserRegistrationSerializer
    permission_classes = [AllowAny]

    def create(self, request: Request, *args: object, **kwargs: object) -> Response:
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        return Response(
            UserProfileSerializer(user, context={"request": request}).data,
            status=status.HTTP_201_CREATED,
        )


@extend_schema(tags=["Auth"])
class CustomTokenObtainPairView(TokenObtainPairView):
    """
    Obtain JWT access and refresh tokens.

    The response also includes basic user metadata.
    """

    serializer_class = CustomTokenObtainPairSerializer  # type: ignore[assignment]
    permission_classes = [AllowAny]  # type: ignore[assignment]

    @extend_schema(
        summary="Login - obtain JWT token pair",
        auth=[],
        responses={
            200: CustomTokenObtainPairSerializer,
            401: OpenApiResponse(description="Invalid credentials"),
        },
    )
    def post(self, request: Request, *args: object, **kwargs: object) -> Response:
        return super().post(request, *args, **kwargs)


@extend_schema(tags=["Auth"])
class CustomTokenRefreshView(TokenRefreshView):
    """Refresh a JWT access token using a valid refresh token."""

    @extend_schema(
        summary="Refresh access token",
        auth=[],
    )
    def post(self, request: Request, *args: object, **kwargs: object) -> Response:
        return super().post(request, *args, **kwargs)


@extend_schema(tags=["Auth"])
@extend_schema_view(
    get=extend_schema(summary="Retrieve own profile"),
    patch=extend_schema(summary="Partially update own profile"),
    put=extend_schema(summary="Update own profile"),
)
class ProfileView(generics.RetrieveUpdateAPIView):  # type: ignore[type-arg]
    """Retrieve or update the authenticated user's own profile."""

    serializer_class = UserProfileSerializer
    permission_classes = [IsAuthenticated]

    def get_object(self) -> Any:  # type: ignore[override]
        return self.request.user
