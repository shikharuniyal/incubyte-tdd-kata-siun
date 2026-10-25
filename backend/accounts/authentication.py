from rest_framework.authentication import BaseAuthentication
from rest_framework.exceptions import AuthenticationFailed

from .tokens import InvalidToken, user_from_access_token


class JWTAuthentication(BaseAuthentication):
    """Authenticates requests that send `Authorization: Bearer <access token>`."""

    keyword = "Bearer"

    def authenticate(self, request):
        header = request.META.get("HTTP_AUTHORIZATION")
        if not header:
            return None  # Anonymous; the view's permissions decide what happens next.

        parts = header.split()
        if len(parts) != 2 or parts[0] != self.keyword:
            raise AuthenticationFailed("Authorization header must be 'Bearer <token>'.")

        try:
            user = user_from_access_token(parts[1])
        except InvalidToken as exc:
            raise AuthenticationFailed("Invalid or expired token.") from exc
        return user, parts[1]

    def authenticate_header(self, request):
        # Returning a value makes DRF answer 401 (not 403) to unauthenticated requests.
        return self.keyword
