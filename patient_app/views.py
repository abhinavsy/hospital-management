from rest_framework import viewsets
from rest_framework.response import Response
from rest_framework.views import APIView

from core.models import Appointment, Invoice, MedicalRecord
from core.permissions import IsOwnPatientRecord, IsPatientUser
from core.serializers import (
    AppointmentSerializer,
    InvoiceSerializer,
    MedicalRecordSerializer,
    PatientSerializer,
)


class MeView(APIView):
    """GET -> the logged-in patient's own Patient record."""

    permission_classes = [IsPatientUser]

    def get(self, request):
        return Response(PatientSerializer(request.user.profile.patient).data)


class MyAppointmentViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = AppointmentSerializer
    permission_classes = [IsPatientUser, IsOwnPatientRecord]

    def get_queryset(self):
        return Appointment.objects.filter(patient=self.request.user.profile.patient)


class MyMedicalRecordViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = MedicalRecordSerializer
    permission_classes = [IsPatientUser, IsOwnPatientRecord]

    def get_queryset(self):
        return MedicalRecord.objects.filter(
            appointment__patient=self.request.user.profile.patient
        )


class MyInvoiceViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = InvoiceSerializer
    permission_classes = [IsPatientUser, IsOwnPatientRecord]

    def get_queryset(self):
        return Invoice.objects.filter(patient=self.request.user.profile.patient)
