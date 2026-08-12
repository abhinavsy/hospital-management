import uuid
from typing import ClassVar

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models


# Create your models here.
class TimeStampedModel(models.Model):

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class Hospital(TimeStampedModel):
    name = models.CharField(max_length=150, unique=True)
    address = models.TextField(blank=True)
    phone = models.CharField(max_length=20, blank=True)
    email = models.EmailField(blank=True)
    hospital_code = models.CharField(max_length=50, unique=True)

    def __str__(self):
        return self.name


class Department(TimeStampedModel):
    hospital = models.ForeignKey(
        Hospital, on_delete=models.PROTECT, related_name="departments"
    )
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)

    class Meta:
        constraints: ClassVar = [
            models.UniqueConstraint(
                fields=["hospital", "name"], name="unique_department_per_hospital"
            )
        ]

    def __str__(self):
        return self.name


class Doctor(TimeStampedModel):
    department = models.ForeignKey(
        Department, on_delete=models.PROTECT, related_name="doctors"
    )
    doctor_id = models.UUIDField(default=uuid.uuid4, primary_key=True)
    name = models.CharField(max_length=150)
    license_number = models.CharField(max_length=100, unique=True)
    specialization = models.CharField(max_length=150)
    phone = models.CharField(max_length=20)
    joining_date = models.DateField()
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.name


class Patient(TimeStampedModel):
    patient_number = models.CharField(max_length=30, unique=True)
    patient_id = models.UUIDField(
        default=uuid.uuid4, editable=False, unique=True, primary_key=True
    )
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    date_of_birth = models.DateField()
    gender = models.CharField(max_length=20)
    blood_group = models.CharField(max_length=5, blank=True)

    hospitals = models.ManyToManyField(
        Hospital, through="PatientHospital", related_name="patients"
    )

    phone = models.CharField(max_length=20)
    email = models.EmailField(blank=True)
    address = models.TextField(blank=True)
    emergency_contact = models.CharField(max_length=20, blank=True)

    def __str__(self):
        return f"{self.first_name} {self.last_name}"


class PatientHospital(TimeStampedModel):
    patient = models.ForeignKey(
        Patient, on_delete=models.PROTECT, related_name="hospital_records"
    )

    hospital = models.ForeignKey(
        Hospital, on_delete=models.PROTECT, related_name="patient_records"
    )

    registration_number = models.CharField(max_length=50)
    registered_at = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        constraints: ClassVar = [
            models.UniqueConstraint(
                fields=["patient", "hospital"], name="unique_patient_hospital"
            )
        ]

    def __str__(self):
        return f"{self.patient} - {self.hospital}"


class Appointment(TimeStampedModel):

    class Status(models.TextChoices):
        SCHEDULED = "SCHEDULED", "Scheduled"
        CONFIRMED = "CONFIRMED", "Confirmed"
        COMPLETED = "COMPLETED", "Completed"
        CANCELLED = "CANCELLED", "Cancelled"
        NO_SHOW = "NO_SHOW", "No Show"

    patient = models.ForeignKey(
        Patient, on_delete=models.PROTECT, related_name="appointments"
    )
    hospital = models.ForeignKey(
        Hospital, on_delete=models.PROTECT, related_name="appointments"
    )
    doctor = models.ForeignKey(
        Doctor, on_delete=models.PROTECT, related_name="appointments"
    )

    appointment_date = models.DateField()
    start_time = models.TimeField()
    end_time = models.TimeField()

    status = models.CharField(
        max_length=20, choices=Status.choices, default=Status.SCHEDULED
    )

    reason = models.TextField(blank=True)
    notes = models.TextField(blank=True)

    def __str__(self):
        return f"{self.patient} - {self.doctor}"


class MedicalRecord(TimeStampedModel):
    appointment = models.OneToOneField(
        Appointment, on_delete=models.PROTECT, related_name="medical_record"
    )

    symptoms = models.TextField()
    diagnosis = models.TextField()
    treatment = models.TextField(blank=True)
    notes = models.TextField(blank=True)


class Prescription(TimeStampedModel):
    medical_record = models.ForeignKey(
        MedicalRecord, on_delete=models.PROTECT, related_name="prescriptions"
    )

    prescribed_at = models.DateTimeField(auto_now_add=True)
    notes = models.TextField(blank=True)


class PrescriptionItem(TimeStampedModel):
    prescription = models.ForeignKey(
        Prescription, on_delete=models.CASCADE, related_name="items"
    )

    # String reference avoids a core <-> pharmacy_app import cycle
    # (pharmacy_app.models already imports TimeStampedModel from here).
    medicine = models.ForeignKey(
        "pharmacy_app.Medicine",
        on_delete=models.PROTECT,
        related_name="prescription_items",
    )
    dosage = models.CharField(max_length=100)
    frequency = models.CharField(max_length=100)
    duration_days = models.PositiveIntegerField()

    instructions = models.TextField(blank=True)


class Invoice(TimeStampedModel):

    class Status(models.TextChoices):
        PENDING = "PENDING", "Pending"
        PARTIAL = "PARTIAL", "Partial"
        PAID = "PAID", "Paid"
        CANCELLED = "CANCELLED", "Cancelled"

    patient = models.ForeignKey(
        Patient, on_delete=models.PROTECT, related_name="invoices"
    )

    invoice_number = models.CharField(max_length=30, unique=True)

    subtotal = models.DecimalField(max_digits=12, decimal_places=2)

    tax = models.DecimalField(max_digits=12, decimal_places=2, default=0)

    total = models.DecimalField(max_digits=12, decimal_places=2)

    status = models.CharField(
        max_length=20, choices=Status.choices, default=Status.PENDING
    )


class InvoiceItem(TimeStampedModel):
    invoice = models.ForeignKey(Invoice, on_delete=models.CASCADE, related_name="items")

    description = models.CharField(max_length=255)

    quantity = models.PositiveIntegerField(default=1)

    unit_price = models.DecimalField(max_digits=10, decimal_places=2)

    amount = models.DecimalField(max_digits=12, decimal_places=2)


class Payment(TimeStampedModel):

    STATUS_CHOICES = [
        ("PENDING", "Pending"),
        ("SUCCESS", "Success"),
        ("FAILED", "Failed"),
    ]

    class PaymentType(models.TextChoices):
        APPOINTMENT = "APPOINTMENT", "Appointment"
        PRESCRIPTION = "PRESCRIPTION", "Prescription"

    order_id = models.CharField(
        max_length=100,
        unique=True,
    )

    patient_id = models.ForeignKey(
        Patient, on_delete=models.PROTECT, related_name="payments"
    )

    payment_type = models.CharField(max_length=20, choices=PaymentType.choices)

    # Exactly one of these should be set, matching `payment_type` - enforced in clean().
    appointment = models.ForeignKey(
        Appointment,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="payments",
    )
    prescription = models.ForeignKey(
        Prescription,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="payments",
    )

    amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
    )

    currency = models.CharField(
        max_length=3,
        default="INR",
    )

    transaction_id = models.CharField(
        max_length=100,
        blank=True,
        null=True,
    )

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="PENDING",
    )

    gateway = models.CharField(
        max_length=50,
        default="PAYTM",
    )

    is_refunded = models.BooleanField(default=False)

    payment_completed = models.BooleanField(default=False)

    def clean(self):
        required_field = {
            self.PaymentType.APPOINTMENT: "appointment",
            self.PaymentType.PRESCRIPTION: "prescription",
        }.get(self.payment_type)

        if required_field and getattr(self, required_field) is None:
            raise ValidationError(
                {required_field: f"Required for payment type {self.payment_type}."}
            )

    def __str__(self):
        return self.order_id


class UserProfile(TimeStampedModel):
    """Links a login account to a role and the domain object that role acts as.

    Access control is driven entirely by `role` plus whichever of
    `patient`/`doctor`/`department`/`hospital` is set for that role - see
    `core/permissions.py` for how each role's queryset scoping is derived
    from these fields.
    """

    class Role(models.TextChoices):
        PATIENT = "PATIENT", "Patient"
        DOCTOR = "DOCTOR", "Doctor"
        DEPARTMENT_ADMIN = "DEPARTMENT_ADMIN", "Department Admin"
        HOSPITAL_ADMIN = "HOSPITAL_ADMIN", "Hospital Admin"
        PHARMACIST = "PHARMACIST", "Pharmacist"

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="profile"
    )
    role = models.CharField(max_length=20, choices=Role.choices)

    # Exactly one of these should be set, matching `role` - enforced in clean().
    patient = models.OneToOneField(
        Patient,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="user_profile",
    )
    doctor = models.OneToOneField(
        Doctor,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="user_profile",
    )
    department = models.ForeignKey(
        Department,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="admin_profiles",
    )
    hospital = models.ForeignKey(
        Hospital,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="admin_profiles",
    )

    def clean(self):
        required_field = {
            self.Role.PATIENT: "patient",
            self.Role.DOCTOR: "doctor",
            self.Role.DEPARTMENT_ADMIN: "department",
            self.Role.HOSPITAL_ADMIN: "hospital",
            # A pharmacist works a specific hospital's pharmacy - reuses the
            # same `hospital` link as HOSPITAL_ADMIN.
            self.Role.PHARMACIST: "hospital",
        }.get(self.role)

        if required_field and getattr(self, required_field) is None:
            raise ValidationError({required_field: f"Required for role {self.role}."})

    def __str__(self):
        return f"{self.user.username} ({self.role})"
