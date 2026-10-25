"""Makes, models, physical vehicles (VINs) and the listings sold through the API."""

import uuid

from django.db import models
from django.utils import timezone

from .parties import Dealership, Manufacturer


class Make(models.Model):
    """A customer-facing brand, e.g. "Toyota", produced by a manufacturer."""

    make_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    manufacturer = models.ForeignKey(
        Manufacturer, on_delete=models.PROTECT, db_column="manufacturer_id", related_name="makes"
    )
    name = models.TextField()

    class Meta:
        managed = False
        db_table = "make"


class VehicleModel(models.Model):
    """A specification shared by many cars, e.g. Toyota Corolla 2024 BASE."""

    model_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    make = models.ForeignKey(Make, on_delete=models.PROTECT, db_column="make_id", related_name="models")
    name = models.TextField()
    model_year = models.IntegerField()
    variant = models.TextField(default="BASE")
    category = models.TextField()
    fuel_type = models.TextField(null=True, blank=True)
    transmission = models.TextField(null=True, blank=True)

    class Meta:
        managed = False
        db_table = "vehicle_model"


class Vehicle(models.Model):
    """One physical car, identified by its VIN for its whole life."""

    vehicle_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    vehicle_model = models.ForeignKey(
        VehicleModel, on_delete=models.PROTECT, db_column="model_id", related_name="vehicles"
    )
    vin = models.TextField(unique=True)
    colour = models.TextField(null=True, blank=True)
    first_registration_date = models.DateField(null=True, blank=True)
    current_odometer = models.IntegerField(default=0)
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        managed = False
        db_table = "vehicle"


class VehicleListing(models.Model):
    """
    What a dealership offers for sale: a model at a price.

    This is the "vehicle" resource of the kata API. Its quantity is not
    stored; it is the number of AVAILABLE acquisitions (see VehicleInventory).
    """

    class Condition(models.TextChoices):
        NEW = "NEW"
        USED = "USED"
        REFURBISHED = "REFURBISHED"

    class Status(models.TextChoices):
        ACTIVE = "ACTIVE"
        ARCHIVED = "ARCHIVED"

    listing_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    dealership = models.ForeignKey(
        Dealership, on_delete=models.PROTECT, db_column="dealership_id", related_name="listings"
    )
    vehicle_model = models.ForeignKey(
        VehicleModel, on_delete=models.PROTECT, db_column="model_id", related_name="listings"
    )
    condition_class = models.TextField(choices=Condition.choices)
    advertised_price = models.DecimalField(max_digits=14, decimal_places=2)
    currency_code = models.CharField(max_length=3, default="INR")
    status = models.TextField(choices=Status.choices, default=Status.ACTIVE)
    deleted_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        managed = False
        db_table = "vehicle_listing"


class VehicleInventory(models.Model):
    """Read-only model over the vehicle_inventory view (one row per non-deleted listing)."""

    id = models.UUIDField(primary_key=True)
    dealership = models.ForeignKey(
        Dealership, on_delete=models.DO_NOTHING, db_column="dealership_id", related_name="+"
    )
    make = models.TextField()
    model_name = models.TextField(db_column="model")
    category = models.TextField()
    condition_class = models.TextField()
    price = models.DecimalField(max_digits=14, decimal_places=2)
    currency_code = models.CharField(max_length=3)
    quantity = models.IntegerField()
    status = models.TextField()

    class Meta:
        managed = False
        db_table = "vehicle_inventory"
