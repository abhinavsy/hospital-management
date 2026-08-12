from typing import ClassVar

from django.db import models

from core.models import TimeStampedModel


class Medicine(TimeStampedModel):

    class Category(models.TextChoices):
        TABLET = "TABLET", "Tablet"
        CAPSULE = "CAPSULE", "Capsule"
        SYRUP = "SYRUP", "Syrup"
        INJECTION = "INJECTION", "Injection"
        OINTMENT = "OINTMENT", "Ointment"
        DROPS = "DROPS", "Drops"
        OTHER = "OTHER", "Other"

    name = models.CharField(max_length=200)
    generic_name = models.CharField(max_length=200, blank=True)
    manufacturer = models.CharField(max_length=150, blank=True)
    category = models.CharField(
        max_length=20, choices=Category.choices, default=Category.TABLET
    )

    batch_number = models.CharField(max_length=50, blank=True)
    unit_price = models.DecimalField(max_digits=10, decimal_places=2)
    stock_quantity = models.PositiveIntegerField(default=0)
    expiry_date = models.DateField(null=True, blank=True)

    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        constraints: ClassVar = [
            models.UniqueConstraint(
                fields=["name", "batch_number"], name="unique_medicine_batch"
            )
        ]

    def __str__(self):
        return f"{self.name} ({self.batch_number})" if self.batch_number else self.name
