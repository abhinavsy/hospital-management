from rest_framework import serializers

from core.models import PrescriptionItem
from pharmacy_app.models import Medicine


class MedicineSerializer(serializers.ModelSerializer):
    class Meta:
        model = Medicine
        fields = [
            "id",
            "name",
            "generic_name",
            "manufacturer",
            "category",
            "batch_number",
            "unit_price",
            "stock_quantity",
            "expiry_date",
            "description",
            "is_active",
        ]


class MedicineSummarySerializer(serializers.ModelSerializer):
    """Embedded in PrescriptionItem - enough for a pharmacist to price/identify it."""

    class Meta:
        model = Medicine
        fields = ["id", "name", "category", "unit_price"]


class PrescribedItemSerializer(serializers.ModelSerializer):
    """A prescribed medicine, with price, for the pharmacist's dispensing queue."""

    medicine = MedicineSummarySerializer(read_only=True)
    patient_name = serializers.SerializerMethodField()
    doctor_name = serializers.SerializerMethodField()
    prescribed_at = serializers.DateTimeField(
        source="prescription.prescribed_at", read_only=True
    )

    class Meta:
        model = PrescriptionItem
        fields = [
            "id",
            "medicine",
            "dosage",
            "frequency",
            "duration_days",
            "instructions",
            "patient_name",
            "doctor_name",
            "prescribed_at",
        ]

    def get_patient_name(self, obj):
        patient = obj.prescription.medical_record.appointment.patient
        return f"{patient.first_name} {patient.last_name}"

    def get_doctor_name(self, obj):
        return obj.prescription.medical_record.appointment.doctor.name
