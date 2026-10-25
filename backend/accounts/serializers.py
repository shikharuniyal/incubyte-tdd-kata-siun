from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError as DjangoValidationError
from rest_framework import serializers

from dealership.models import AppUser

from .roles import Role, active_role_assignments
from .services import email_is_registered, normalize_email

DUPLICATE_EMAIL_MESSAGE = "An account with this email already exists."


class RegisterSerializer(serializers.Serializer):
    first_name = serializers.CharField(max_length=100)
    last_name = serializers.CharField(max_length=100)
    email = serializers.EmailField(max_length=254)
    password = serializers.CharField(write_only=True, max_length=128, trim_whitespace=False)

    def validate_email(self, value: str) -> str:
        email = normalize_email(value)
        if email_is_registered(email):
            raise serializers.ValidationError(DUPLICATE_EMAIL_MESSAGE)
        return email

    def validate_password(self, value: str) -> str:
        try:
            validate_password(value)
        except DjangoValidationError as exc:
            raise serializers.ValidationError(list(exc.messages)) from exc
        return value


class LoginSerializer(serializers.Serializer):
    email = serializers.CharField(max_length=254)
    password = serializers.CharField(max_length=128, trim_whitespace=False)


class RefreshTokenSerializer(serializers.Serializer):
    refresh = serializers.CharField(max_length=512)


def user_payload(user: AppUser) -> dict:
    """The public description of a user, including their dealership roles."""
    roles = [
        {
            "dealership_id": str(assignment.dealership_id),
            "dealership_name": assignment.dealership.name,
            "role": assignment.role,
        }
        for assignment in active_role_assignments(user)
    ]
    return {
        "id": str(user.user_id),
        "email": user.email,
        "name": user.person.party.display_name,
        "roles": roles,
        "is_admin": any(role["role"] == Role.ADMIN for role in roles),
        "is_staff": bool(roles),
    }
