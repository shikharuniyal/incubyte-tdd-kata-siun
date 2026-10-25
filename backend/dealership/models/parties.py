"""People, organisations and the business roles they play (customer, manufacturer, dealer)."""

import uuid

from django.db import models
from django.utils import timezone


class Party(models.Model):
    """Anyone who can own, buy, sell or supply a car: a person or an organisation."""

    class Type(models.TextChoices):
        PERSON = "PERSON"
        ORGANIZATION = "ORGANIZATION"

    party_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    party_type = models.TextField(choices=Type.choices)
    display_name = models.TextField()
    email = models.TextField(null=True, blank=True)
    phone = models.TextField(null=True, blank=True)
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        managed = False
        db_table = "party"


class Person(models.Model):
    party = models.OneToOneField(
        Party, primary_key=True, on_delete=models.PROTECT, db_column="party_id", related_name="person"
    )
    given_name = models.TextField()
    family_name = models.TextField()

    class Meta:
        managed = False
        db_table = "person"


class Organization(models.Model):
    party = models.OneToOneField(
        Party, primary_key=True, on_delete=models.PROTECT, db_column="party_id", related_name="organization"
    )
    registered_name = models.TextField()
    registration_number = models.TextField(null=True, blank=True, unique=True)

    class Meta:
        managed = False
        db_table = "organization"


class Customer(models.Model):
    """The customer role of a party (person or organisation)."""

    party = models.OneToOneField(
        Party, primary_key=True, on_delete=models.PROTECT, db_column="party_id", related_name="customer"
    )
    notes = models.TextField(null=True, blank=True)
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        managed = False
        db_table = "customer"


class Manufacturer(models.Model):
    """The manufacturer role of an organisation."""

    manufacturer_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    organization = models.OneToOneField(
        Organization,
        on_delete=models.PROTECT,
        db_column="organization_party_id",
        related_name="manufacturer",
    )

    class Meta:
        managed = False
        db_table = "manufacturer"


class DealerOrganization(models.Model):
    """The legal business that operates one or more dealerships."""

    dealer_org_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    organization = models.OneToOneField(
        Organization,
        on_delete=models.PROTECT,
        db_column="organization_party_id",
        related_name="dealer_organization",
    )
    gstin = models.TextField(null=True, blank=True, unique=True)

    class Meta:
        managed = False
        db_table = "dealer_organization"


class Dealership(models.Model):
    class Status(models.TextChoices):
        ACTIVE = "ACTIVE"
        INACTIVE = "INACTIVE"

    dealership_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    dealer_org = models.ForeignKey(
        DealerOrganization, on_delete=models.PROTECT, db_column="dealer_org_id", related_name="dealerships"
    )
    name = models.TextField()
    status = models.TextField(choices=Status.choices, default=Status.ACTIVE)

    class Meta:
        managed = False
        db_table = "dealership"

    @property
    def owner_party(self) -> Party:
        """The party that legally owns cars stocked by this dealership."""
        return self.dealer_org.organization.party


class Site(models.Model):
    class Type(models.TextChoices):
        BRANCH = "BRANCH"
        WAREHOUSE = "WAREHOUSE"
        OTHER = "OTHER"

    site_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    dealership = models.ForeignKey(
        Dealership, on_delete=models.PROTECT, db_column="dealership_id", related_name="sites"
    )
    owner_party = models.ForeignKey(
        Party, on_delete=models.PROTECT, db_column="owner_party_id", related_name="+"
    )
    name = models.TextField()
    address = models.TextField()
    site_type = models.TextField(choices=Type.choices)

    class Meta:
        managed = False
        db_table = "site"


class SiteArea(models.Model):
    class Type(models.TextChoices):
        SHOWROOM = "SHOWROOM"
        LOT = "LOT"
        WAREHOUSE = "WAREHOUSE"
        SERVICE_BAY = "SERVICE_BAY"
        OTHER = "OTHER"

    area_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    site = models.ForeignKey(Site, on_delete=models.PROTECT, db_column="site_id", related_name="areas")
    name = models.TextField()
    area_type = models.TextField(choices=Type.choices)
    capacity = models.IntegerField(null=True, blank=True)

    class Meta:
        managed = False
        db_table = "site_area"
