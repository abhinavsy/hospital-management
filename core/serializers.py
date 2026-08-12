"""
Shared serializers for the domain models in `core.models`.

Other apps' serializers (`dashboard_app`, `doctor_app`, `patient_app`)
import and compose these rather than redefining the same model shapes -
this file is the single place a `Doctor`/`Patient`/`Appointment`/etc. is
described for the API.
"""

from rest_framework import serializers

from core.models import (
    Appointment,
    Department,
    Doctor,
    Hospital,
    Invoice,
    InvoiceItem,
    MedicalRecord,
    Patient,
    Prescription,
    PrescriptionItem,
    UserProfile,
)
from pharmacy_app.models import Medicine
from pharmacy_app.serializers import MedicineSummarySerializer


class HospitalSerializer(serializers.ModelSerializer):
    class Meta:
        model = Hospital
        fields = ["id", "name", "address", "phone", "email", "hospital_code"]


class HospitalSummarySerializer(serializers.ModelSerializer):
    class Meta:
        model = Hospital
        fields = ["id", "name", "hospital_code"]


class DepartmentSerializer(serializers.ModelSerializer):
    hospital = HospitalSummarySerializer(read_only=True)
    hospital_id = serializers.PrimaryKeyRelatedField(
        source="hospital", queryset=Hospital.objects.all(), write_only=True
    )

    class Meta:
        model = Department
        fields = ["id", "name", "description", "hospital", "hospital_id"]


class DepartmentSummarySerializer(serializers.ModelSerializer):
    class Meta:
        model = Department
        fields = ["id", "name"]


class DoctorSerializer(serializers.ModelSerializer):
    department = DepartmentSummarySerializer(read_only=True)
    department_id = serializers.PrimaryKeyRelatedField(
        source="department", queryset=Department.objects.all(), write_only=True
    )

    class Meta:
        model = Doctor
        fields = [
            "doctor_id",
            "department",
            "department_id",
            "name",
            "license_number",
            "specialization",
            "phone",
            "joining_date",
            "is_active",
        ]
        read_only_fields = ["doctor_id"]


class DoctorSummarySerializer(serializers.ModelSerializer):
    department = DepartmentSummarySerializer(read_only=True)

    class Meta:
        model = Doctor
        fields = ["doctor_id", "name", "specialization", "department"]


class PatientSerializer(serializers.ModelSerializer):
    class Meta:
        model = Patient
        fields = [
            "patient_id",
            "patient_number",
            "first_name",
            "last_name",
            "date_of_birth",
            "gender",
            "blood_group",
            "phone",
            "email",
            "address",
            "emergency_contact",
        ]
        read_only_fields = ["patient_id", "patient_number"]


class PatientSummarySerializer(serializers.ModelSerializer):
    class Meta:
        model = Patient
        fields = ["patient_id", "patient_number", "first_name", "last_name"]


class AppointmentSerializer(serializers.ModelSerializer):
    patient = PatientSummarySerializer(read_only=True)
    doctor = DoctorSummarySerializer(read_only=True)
    hospital = HospitalSummarySerializer(read_only=True)

    class Meta:
        model = Appointment
        fields = [
            "id",
            "patient",
            "doctor",
            "hospital",
            "appointment_date",
            "start_time",
            "end_time",
            "status",
            "reason",
            "notes",
        ]


class MedicalRecordSerializer(serializers.ModelSerializer):
    class Meta:
        model = MedicalRecord
        fields = ["id", "appointment", "symptoms", "diagnosis", "treatment", "notes"]
        read_only_fields = ["appointment"]


class PrescriptionItemSerializer(serializers.ModelSerializer):
    """`medicine_id` is what the doctor picks (from the pharmacy_app catalog);
    `medicine` is the read-only nested summary (name/category/price) so the
    doctor and, later, the pharmacist both see what was actually selected."""

    medicine = MedicineSummarySerializer(read_only=True)
    medicine_id = serializers.PrimaryKeyRelatedField(
        source="medicine", queryset=Medicine.objects.all(), write_only=True
    )

    class Meta:
        model = PrescriptionItem
        fields = [
            "id",
            "medicine",
            "medicine_id",
            "dosage",
            "frequency",
            "duration_days",
            "instructions",
        ]


class PrescriptionSerializer(serializers.ModelSerializer):
    items = PrescriptionItemSerializer(many=True)

    class Meta:
        model = Prescription
        fields = ["id", "medical_record", "prescribed_at", "notes", "items"]
        read_only_fields = ["medical_record", "prescribed_at"]

    def create(self, validated_data):
        items_data = validated_data.pop("items")
        prescription = Prescription.objects.create(**validated_data)
        PrescriptionItem.objects.bulk_create(
            PrescriptionItem(prescription=prescription, **item) for item in items_data
        )
        return prescription


class InvoiceItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = InvoiceItem
        fields = ["id", "description", "quantity", "unit_price", "amount"]


class InvoiceSerializer(serializers.ModelSerializer):
    items = InvoiceItemSerializer(many=True, read_only=True)
    patient = PatientSummarySerializer(read_only=True)

    class Meta:
        model = Invoice
        fields = [
            "id",
            "patient",
            "invoice_number",
            "subtotal",
            "tax",
            "total",
            "status",
            "items",
        ]


class UserProfileSerializer(serializers.ModelSerializer):
    username = serializers.CharField(source="user.username", read_only=True)
    email = serializers.CharField(source="user.email", read_only=True)
    patient = PatientSummarySerializer(read_only=True)
    doctor = DoctorSummarySerializer(read_only=True)
    department = DepartmentSummarySerializer(read_only=True)
    hospital = HospitalSummarySerializer(read_only=True)

    class Meta:
        model = UserProfile
        fields = [
            "username",
            "email",
            "role",
            "patient",
            "doctor",
            "department",
            "hospital",
        ]
