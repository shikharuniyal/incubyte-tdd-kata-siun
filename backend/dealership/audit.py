"""Recording the audit trail. Call inside the same transaction as the change it describes."""

from uuid import UUID

from .models import AppUser, AuditEvent


def record(*, actor: AppUser | None, action: str, entity_type: str, entity_id: UUID, **details) -> AuditEvent:
    return AuditEvent.objects.create(
        actor_user=actor,
        action=action,
        entity_type=entity_type,
        entity_id=entity_id,
        details={key: _json_safe(value) for key, value in details.items()},
    )


def _json_safe(value):
    if isinstance(value, (list, tuple)):
        return [_json_safe(item) for item in value]
    if isinstance(value, (str, int, float, bool)) or value is None:
        return value
    return str(value)  # UUIDs, Decimals, datetimes
