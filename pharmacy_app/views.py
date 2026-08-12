from rest_framework import viewsets

from core.models import PrescriptionItem
from core.permissions import IsPharmacistUser
from pharmacy_app.models import Medicine
from pharmacy_app.serializers import MedicineSerializer, PrescribedItemSerializer


class MedicineViewSet(viewsets.ReadOnlyModelViewSet):
    """The shared medicine catalog with prices - not hospital-scoped, since
    stock/pricing is a single inventory in the current schema."""

    serializer_class = MedicineSerializer
    permission_classes = [IsPharmacistUser]
    queryset = Medicine.objects.filter(is_active=True)


class PrescribedItemViewSet(viewsets.ReadOnlyModelViewSet):
    """What doctors have actually prescribed (medicine + price + who/for whom),
    scoped to the prescriptions written within the pharmacist's own hospital."""

    serializer_class = PrescribedItemSerializer
    permission_classes = [IsPharmacistUser]

    def get_queryset(self):
        hospital = self.request.user.profile.hospital
        return (
            PrescriptionItem.objects.filter(
                prescription__medical_record__appointment__hospital=hospital
            )
            .select_related(
                "medicine",
                "prescription",
                "prescription__medical_record__appointment__patient",
                "prescription__medical_record__appointment__doctor",
            )
            .order_by("-prescription__prescribed_at")
        )
