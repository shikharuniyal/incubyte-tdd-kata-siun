"""Sales: a sale contains one item per sold acquisition (a stock period of one car)."""

import uuid

from django.db import models
from django.utils import timezone

from .access import AppUser
from .parties import Customer, Dealership
from .stock import Acquisition


class Sale(models.Model):
    class Status(models.TextChoices):
        DRAFT = "DRAFT"
        COMPLETED = "COMPLETED"
        CANCELLED = "CANCELLED"
        REFUNDED = "REFUNDED"

    sale_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    dealership = models.ForeignKey(Dealership, on_delete=models.PROTECT, db_column="dealership_id", related_name="sales")
    buyer = models.ForeignKey(
        Customer, on_delete=models.PROTECT, db_column="buyer_customer_party_id", related_name="purchases"
    )
    created_by = models.ForeignKey(AppUser, on_delete=models.PROTECT, db_column="created_by_user_id", related_name="+")
    authorized_by = models.ForeignKey(
        AppUser, on_delete=models.PROTECT, db_column="authorized_by_user_id", null=True, blank=True, related_name="+"
    )
    status = models.TextField(choices=Status.choices, default=Status.DRAFT)
    total_amount = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    currency_code = models.CharField(max_length=3, default="INR")
    created_at = models.DateTimeField(default=timezone.now)
    completed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        managed = False
        db_table = "sale"


class SaleItem(models.Model):
    sale_item_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    sale = models.ForeignKey(Sale, on_delete=models.PROTECT, db_column="sale_id", related_name="items")
    acquisition = models.OneToOneField(
        Acquisition, on_delete=models.PROTECT, db_column="acquisition_id", related_name="sale_item"
    )
    dealership = models.ForeignKey(Dealership, on_delete=models.PROTECT, db_column="dealership_id", related_name="+")
    agreed_price = models.DecimalField(max_digits=14, decimal_places=2)
    discount = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    tax_amount = models.DecimalField(max_digits=14, decimal_places=2, default=0)

    class Meta:
        managed = False
        db_table = "sale_item"
