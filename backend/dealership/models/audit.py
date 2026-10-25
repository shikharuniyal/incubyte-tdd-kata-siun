import uuid

from django.db import models
from django.utils import timezone

from .access import AppUser


class AuditEvent(models.Model):
    """Who did what to which record, and when."""

    audit_event_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    actor_user = models.ForeignKey(
        AppUser, on_delete=models.PROTECT, db_column="actor_user_id", null=True, blank=True, related_name="+"
    )
    entity_type = models.TextField()
    entity_id = models.UUIDField()
    action = models.TextField()
    details = models.JSONField(default=dict)
    occurred_at = models.DateTimeField(default=timezone.now)

    class Meta:
        managed = False
        db_table = "audit_event"
