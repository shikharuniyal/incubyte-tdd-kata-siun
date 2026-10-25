"""
Token issuing and verification.

* Access tokens are short-lived, signed JWTs (stateless).
* Refresh tokens are random strings. Only their SHA-256 hash is stored, in
  the auth_session table, so they can be rotated on every use and revoked
  on logout.
"""

import hashlib
import secrets
from dataclasses import dataclass

import jwt
from django.conf import settings
from django.db import transaction
from django.utils import timezone

from dealership.models import AppUser, AuthSession

ACCESS_TOKEN_TYPE = "access"


class InvalidToken(Exception):
    """The token is missing, malformed, expired, revoked or belongs to an inactive user."""


@dataclass(frozen=True)
class TokenPair:
    access: str
    refresh: str


def issue_access_token(user: AppUser) -> str:
    config = settings.JWT_SETTINGS
    now = timezone.now()
    payload = {
        "sub": str(user.user_id),
        "type": ACCESS_TOKEN_TYPE,
        "iat": now,
        "exp": now + config["ACCESS_TOKEN_LIFETIME"],
    }
    return jwt.encode(payload, config["SIGNING_KEY"], algorithm=config["ALGORITHM"])


def user_from_access_token(token: str) -> AppUser:
    config = settings.JWT_SETTINGS
    try:
        payload = jwt.decode(
            token,
            config["SIGNING_KEY"],
            algorithms=[config["ALGORITHM"]],
            options={"require": ["exp", "sub", "type"]},
        )
    except jwt.PyJWTError as exc:
        raise InvalidToken from exc

    if payload["type"] != ACCESS_TOKEN_TYPE:
        raise InvalidToken
    user = AppUser.objects.filter(user_id=payload["sub"], is_active=True).first()
    if user is None:
        raise InvalidToken
    return user


def issue_token_pair(user: AppUser) -> TokenPair:
    raw_refresh = secrets.token_urlsafe(48)
    AuthSession.objects.create(
        user=user,
        refresh_token_hash=_hash(raw_refresh),
        expires_at=timezone.now() + settings.JWT_SETTINGS["REFRESH_TOKEN_LIFETIME"],
    )
    return TokenPair(access=issue_access_token(user), refresh=raw_refresh)


@transaction.atomic
def rotate_refresh_token(raw_refresh: str) -> TokenPair:
    """Spend a refresh token: revoke it and return a fresh pair. Reuse is rejected."""
    session = _lock_active_session(raw_refresh)
    session.revoked_at = timezone.now()
    session.save(update_fields=["revoked_at"])
    return issue_token_pair(session.user)


@transaction.atomic
def revoke_refresh_token(raw_refresh: str) -> None:
    """Log out. Revoking an unknown or already revoked token is a no-op."""
    try:
        session = _lock_active_session(raw_refresh)
    except InvalidToken:
        return
    session.revoked_at = timezone.now()
    session.save(update_fields=["revoked_at"])


def _lock_active_session(raw_refresh: str) -> AuthSession:
    session = (
        AuthSession.objects.select_for_update(of=("self",))
        .select_related("user")
        .filter(
            refresh_token_hash=_hash(raw_refresh),
            revoked_at__isnull=True,
            expires_at__gt=timezone.now(),
        )
        .first()
    )
    if session is None or not session.user.is_active:
        raise InvalidToken
    return session


def _hash(raw_token: str) -> str:
    return hashlib.sha256(raw_token.encode("utf-8")).hexdigest()
