from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from . import services, tokens
from .serializers import (
    DUPLICATE_EMAIL_MESSAGE,
    LoginSerializer,
    RefreshTokenSerializer,
    RegisterSerializer,
    user_payload,
)

INVALID_CREDENTIALS = {"detail": "Invalid email or password."}
INVALID_REFRESH_TOKEN = {"detail": "Invalid or expired refresh token."}


def session_response(user, pair: tokens.TokenPair, status_code=status.HTTP_200_OK) -> Response:
    return Response(
        {"access": pair.access, "refresh": pair.refresh, "user": user_payload(user)},
        status=status_code,
    )


class PublicAPIView(APIView):
    """Endpoints used before the client holds an access token."""

    authentication_classes: list = []
    permission_classes = [AllowAny]


class RegisterView(PublicAPIView):
    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            user = services.register_user(**serializer.validated_data)
        except services.EmailAlreadyRegistered:
            return Response({"email": [DUPLICATE_EMAIL_MESSAGE]}, status=status.HTTP_400_BAD_REQUEST)
        return session_response(user, tokens.issue_token_pair(user), status.HTTP_201_CREATED)


class LoginView(PublicAPIView):
    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            user = services.authenticate_user(**serializer.validated_data)
        except services.InvalidCredentials:
            return Response(INVALID_CREDENTIALS, status=status.HTTP_401_UNAUTHORIZED)
        return session_response(user, tokens.issue_token_pair(user))


class RefreshView(PublicAPIView):
    def post(self, request):
        serializer = RefreshTokenSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            pair = tokens.rotate_refresh_token(serializer.validated_data["refresh"])
        except tokens.InvalidToken:
            return Response(INVALID_REFRESH_TOKEN, status=status.HTTP_401_UNAUTHORIZED)
        return Response({"access": pair.access, "refresh": pair.refresh})


class LogoutView(PublicAPIView):
    def post(self, request):
        serializer = RefreshTokenSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        tokens.revoke_refresh_token(serializer.validated_data["refresh"])
        return Response(status=status.HTTP_204_NO_CONTENT)


class MeView(APIView):
    def get(self, request):
        return Response(user_payload(request.user))
