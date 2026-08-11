from django.db import models


# Create your models here.
class TimeStampedModel(models.Model):

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)


class Department(TimeStampedModel):
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)

    def __str__(self):
        return self.name


class Doctor(TimeStampedModel):
    department = models.ForeignKey(
        Department, on_delete=models.PROTECT, related_name="doctors"
    )

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

    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    date_of_birth = models.DateField()
    gender = models.CharField(max_length=20)
    blood_group = models.CharField(max_length=5, blank=True)

    phone = models.CharField(max_length=20)
    email = models.EmailField(blank=True)
    address = models.TextField(blank=True)
    emergency_contact = models.CharField(max_length=20, blank=True)

    def __str__(self):
        return f"{self.first_name} {self.last_name}"


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

    medicine_name = models.CharField(max_length=200)
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

    class Status(models.TextChoices):
        PENDING = "PENDING", "Pending"
        SUCCESS = "SUCCESS", "Success"
        FAILED = "FAILED", "Failed"
        REFUNDED = "REFUNDED", "Refunded"

    invoice = models.ForeignKey(
        Invoice, on_delete=models.PROTECT, related_name="payments"
    )

    amount = models.DecimalField(max_digits=12, decimal_places=2)

    transaction_id = models.CharField(max_length=100, unique=True)

    status = models.CharField(
        max_length=20, choices=Status.choices, default=Status.PENDING
    )

    payment_method = models.CharField(max_length=30)

    paid_at = models.DateTimeField(null=True, blank=True)
