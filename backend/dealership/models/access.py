"""Login accounts, dealership roles and refresh-token sessions."""

import uuid

from django.contrib.auth.base_user import AbstractBaseUser, BaseUserManager
from django.db import models
from django.utils import timezone

from .parties import Dealership, Person


class AppUser(AbstractBaseUser):
    """
    A person who can log in. Mapped onto the app_user table.

    Django's password helpers store the hash in the password_hash column.
    """

    user_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    person = models.OneToOneField(
        Person, on_delete=models.PROTECT, db_column="person_party_id", related_name="user"
    )
    email = models.TextField(unique=True)
    password = models.CharField(max_length=128, db_column="password_hash")
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(default=timezone.now)

    # The schema has no last_login column.
    last_login = None

    objects = BaseUserManager()

    USERNAME_FIELD = "email"
    EMAIL_FIELD = "email"
    REQUIRED_FIELDS: list[str] = []

    class Meta:
        managed = False
        db_table = "app_user"


class UserRoleAssignment(models.Model):
    """A user's role at one dealership. A revoked assignment is kept for history."""

    class Role(models.TextChoices):
        ADMIN = "ADMIN"
        MANAGER = "MANAGER"
        STAFF = "STAFF"

    assignment_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        AppUser, on_delete=models.PROTECT, db_column="user_id", related_name="role_assignments"
    )
    dealership = models.ForeignKey(
        Dealership, on_delete=models.PROTECT, db_column="dealership_id", related_name="role_assignments"
    )
    role = models.TextField(choices=Role.choices)
    granted_at = models.DateTimeField(default=timezone.now)
    revoked_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        managed = False
        db_table = "user_role_assignment"


class AuthSession(models.Model):
    """A refresh-token session. Only a SHA-256 hash of the token is stored."""

    session_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(AppUser, on_delete=models.PROTECT, db_column="user_id", related_name="sessions")
    refresh_token_hash = models.TextField(unique=True)
    created_at = models.DateTimeField(default=timezone.now)
    expires_at = models.DateTimeField()
    revoked_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        managed = False
        db_table = "auth_session"
