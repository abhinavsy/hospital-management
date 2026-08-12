from rest_framework import serializers

from core.models import Appointment, MedicalRecord
from core.serializers import (  # noqa: F401
    DoctorSummarySerializer,
    HospitalSummarySerializer,
    MedicalRecordSerializer,
    PatientSummarySerializer,
    PrescriptionSerializer,
)


class MyAppointmentSerializer(serializers.ModelSerializer):
    """Writable appointment serializer for the doctor's own appointments.

    `patient` is client-writable (which patient is being appointed);
    `doctor`/`hospital` are never client-writable - the view derives them
    from the caller's own UserProfile.doctor.
    """

    patient_detail = PatientSummarySerializer(source="patient", read_only=True)
    doctor_detail = DoctorSummarySerializer(source="doctor", read_only=True)
    hospital_detail = HospitalSummarySerializer(source="hospital", read_only=True)

    class Meta:
        model = Appointment
        fields = [
            "id",
            "patient",
            "patient_detail",
            "doctor_detail",
            "hospital_detail",
            "appointment_date",
            "start_time",
            "end_time",
            "status",
            "reason",
            "notes",
        ]


class MyMedicalRecordSerializer(serializers.ModelSerializer):
    class Meta:
        model = MedicalRecord
        fields = ["id", "appointment", "symptoms", "diagnosis", "treatment", "notes"]
        read_only_fields = ["appointment"]
