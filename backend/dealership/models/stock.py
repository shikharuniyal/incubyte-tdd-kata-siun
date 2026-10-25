"""Stock: each acquisition is one period during which a physical car is in a dealership's inventory."""

import uuid

from django.db import models
from django.utils import timezone

from .access import AppUser
from .catalog import Vehicle, VehicleListing, VehicleModel
from .parties import Dealership, Party, SiteArea


class Acquisition(models.Model):
    class Type(models.TextChoices):
        NEW_SUPPLY = "NEW_SUPPLY"
        USED_PURCHASE = "USED_PURCHASE"
        TRADE_IN = "TRADE_IN"
        AUCTION = "AUCTION"
        TRANSFER = "TRANSFER"
        RETURN = "RETURN"
        OTHER = "OTHER"

    class Ownership(models.TextChoices):
        OWNED = "OWNED"
        CONSIGNED = "CONSIGNED"

    class Status(models.TextChoices):
        INTAKE = "INTAKE"
        INSPECTION = "INSPECTION"
        REFURBISHING = "REFURBISHING"
        AVAILABLE = "AVAILABLE"
        RESERVED = "RESERVED"
        SOLD = "SOLD"
        RETURNED = "RETURNED"
        REMOVED = "REMOVED"

    acquisition_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    vehicle = models.ForeignKey(Vehicle, on_delete=models.PROTECT, db_column="vehicle_id", related_name="acquisitions")
    vehicle_model = models.ForeignKey(VehicleModel, on_delete=models.PROTECT, db_column="model_id", related_name="+")
    listing = models.ForeignKey(
        VehicleListing, on_delete=models.PROTECT, db_column="listing_id", related_name="acquisitions"
    )
    dealership = models.ForeignKey(Dealership, on_delete=models.PROTECT, db_column="dealership_id", related_name="+")
    source_party = models.ForeignKey(Party, on_delete=models.PROTECT, db_column="source_party_id", related_name="+")
    current_area = models.ForeignKey(
        SiteArea, on_delete=models.PROTECT, db_column="current_area_id", null=True, blank=True, related_name="+"
    )
    stock_number = models.TextField()
    acquisition_type = models.TextField(choices=Type.choices)
    ownership_type = models.TextField(choices=Ownership.choices)
    inventory_status = models.TextField(choices=Status.choices, default=Status.INTAKE)
    acquisition_cost = models.DecimalField(max_digits=14, decimal_places=2)
    asking_price = models.DecimalField(max_digits=14, decimal_places=2, null=True, blank=True)
    currency_code = models.CharField(max_length=3, default="INR")
    intake_odometer = models.IntegerField(default=0)
    acquired_at = models.DateTimeField(default=timezone.now)
    closed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        managed = False
        db_table = "acquisition"


class OwnershipPeriod(models.Model):
    """Who legally owned a car between two moments. At most one open period per car."""

    ownership_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    vehicle = models.ForeignKey(Vehicle, on_delete=models.PROTECT, db_column="vehicle_id", related_name="ownerships")
    owner_party = models.ForeignKey(Party, on_delete=models.PROTECT, db_column="owner_party_id", related_name="+")
    started_at = models.DateTimeField()
    ended_at = models.DateTimeField(null=True, blank=True)
    reason = models.TextField(null=True, blank=True)

    class Meta:
        managed = False
        db_table = "ownership_period"


class InventoryEvent(models.Model):
    """Append-only ledger of stock changes. The idempotency key stops a retried request applying twice."""

    class Type(models.TextChoices):
        ACQUIRED = "ACQUIRED"
        AVAILABLE = "AVAILABLE"
        RESERVED = "RESERVED"
        RELEASED = "RELEASED"
        SOLD = "SOLD"
        RESTOCKED = "RESTOCKED"
        REFURBISHING = "REFURBISHING"
        REMOVED = "REMOVED"
        RETURNED = "RETURNED"

    inventory_event_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    acquisition = models.ForeignKey(
        Acquisition, on_delete=models.PROTECT, db_column="acquisition_id", related_name="events"
    )
    listing = models.ForeignKey(VehicleListing, on_delete=models.PROTECT, db_column="listing_id", related_name="+")
    performed_by = models.ForeignKey(
        AppUser, on_delete=models.PROTECT, db_column="performed_by_user_id", null=True, blank=True, related_name="+"
    )
    event_type = models.TextField(choices=Type.choices)
    available_quantity_delta = models.IntegerField()
    idempotency_key = models.TextField(unique=True)
    occurred_at = models.DateTimeField(default=timezone.now)

    class Meta:
        managed = False
        db_table = "inventory_event"


class PriceChange(models.Model):
    price_change_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    listing = models.ForeignKey(
        VehicleListing, on_delete=models.PROTECT, db_column="listing_id", related_name="price_changes"
    )
    changed_by = models.ForeignKey(AppUser, on_delete=models.PROTECT, db_column="changed_by_user_id", related_name="+")
    old_price = models.DecimalField(max_digits=14, decimal_places=2)
    new_price = models.DecimalField(max_digits=14, decimal_places=2)
    changed_at = models.DateTimeField(default=timezone.now)

    class Meta:
        managed = False
        db_table = "price_change"
