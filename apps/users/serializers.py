from typing import Any

from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer

User = get_user_model()


class UserRegistrationSerializer(serializers.ModelSerializer[Any]):
    password = serializers.CharField(
        write_only=True,
        required=True,
        validators=[validate_password],
        style={"input_type": "password"},
    )
    password_confirm = serializers.CharField(
        write_only=True,
        required=True,
        style={"input_type": "password"},
    )

    class Meta:
        model = User
        fields = [
            "id",
            "email",
            "first_name",
            "last_name",
            "phone",
            "password",
            "password_confirm",
        ]
        read_only_fields = ["id"]

    def validate(self, attrs: dict[str, Any]) -> dict[str, Any]:
        if attrs["password"] != attrs.pop("password_confirm"):
            raise serializers.ValidationError({"password": "Passwords do not match."})
        return attrs

    def create(self, validated_data: dict[str, Any]) -> Any:
        first_name = validated_data.get("first_name", "")
        last_name = validated_data.get("last_name", "")
        # username is derived from full name; ensure uniqueness by appending email prefix if needed.
        username = f"{first_name} {last_name}".strip() or validated_data["email"].split("@")[0]
        # Guarantee username uniqueness.
        if User.objects.filter(username=username).exists():
            username = f"{username}_{validated_data['email'].split('@')[0]}"

        user = User.objects.create_user(
            email=validated_data["email"],
            username=username,
            first_name=first_name,
            last_name=last_name,
            phone=validated_data.get("phone", ""),
            password=validated_data["password"],
        )
        return user


class UserProfileSerializer(serializers.ModelSerializer[Any]):
    full_name = serializers.CharField(read_only=True)

    class Meta:
        model = User
        fields = [
            "id",
            "email",
            "first_name",
            "last_name",
            "full_name",
            "phone",
            "date_joined",
        ]
        read_only_fields = ["id", "email", "date_joined"]


class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    """Enriches the token response with basic user info."""

    def validate(self, attrs: dict[str, Any]) -> dict[str, Any]:
        data: dict[str, Any] = super().validate(attrs)
        data["user"] = {
            "id": self.user.id,  # type: ignore[union-attr]
            "email": self.user.email,  # type: ignore[union-attr]
            "full_name": self.user.full_name,  # type: ignore[union-attr]
        }
        return data
