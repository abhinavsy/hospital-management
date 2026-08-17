from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from core.models import Appointment, MedicalRecord, Patient
from core.permissions import IsDoctorUser, IsOwnAppointmentDoctor
from core.serializers import PatientSerializer, PrescriptionSerializer

from doctor_app.serializers import MyAppointmentSerializer, MyMedicalRecordSerializer


class DoctorAppointmentViewSet(viewsets.ModelViewSet):
    """The doctor's own appointments: list/retrieve their assigned patients,
    and create/update to schedule ("appoint") or progress an appointment."""

    serializer_class = MyAppointmentSerializer
    permission_classes = [IsDoctorUser, IsOwnAppointmentDoctor]

    def get_queryset(self):
        return Appointment.objects.filter(doctor=self.request.user.profile.doctor)

    def perform_create(self, serializer):
        doctor = self.request.user.profile.doctor
        serializer.save(doctor=doctor, hospital=doctor.department.hospital)

    @action(detail=True, methods=["post"], url_path="medical-record")
    def medical_record(self, request, pk=None):
        appointment = self.get_object()
        record, _ = MedicalRecord.objects.update_or_create(
            appointment=appointment,
            defaults={
                "symptoms": request.data.get("symptoms", ""),
                "diagnosis": request.data.get("diagnosis", ""),
                "treatment": request.data.get("treatment", ""),
                "notes": request.data.get("notes", ""),
            },
        )
        return Response(MyMedicalRecordSerializer(record).data)

    @action(detail=True, methods=["post"], url_path="prescriptions")
    def prescriptions(self, request, pk=None):
        appointment = self.get_object()
        record = getattr(appointment, "medical_record", None)
        if record is None:
            return Response(
                {"detail": "Add a medical record for this appointment first."},
                status=400,
            )
        serializer = PrescriptionSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        prescription = serializer.save(medical_record=record)
        return Response(PrescriptionSerializer(prescription).data, status=201)


class DoctorPatientViewSet(viewsets.ReadOnlyModelViewSet):
    """Read-only: the patients this doctor has been appointed to."""

    serializer_class = PatientSerializer
    permission_classes = [IsDoctorUser]

    def get_queryset(self):
        doctor = self.request.user.profile.doctor
        return Patient.objects.filter(appointments__doctor=doctor).distinct()
