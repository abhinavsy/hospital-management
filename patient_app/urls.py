from django.urls import path
from rest_framework.routers import DefaultRouter

from patient_app.views import (
    MeView,
    MyAppointmentViewSet,
    MyInvoiceViewSet,
    MyMedicalRecordViewSet,
)

app_name = "patient_app"

router = DefaultRouter()
router.register("appointments", MyAppointmentViewSet, basename="my-appointment")
router.register("medical-records", MyMedicalRecordViewSet, basename="my-medical-record")
router.register("invoices", MyInvoiceViewSet, basename="my-invoice")

urlpatterns = [
    path("me/", MeView.as_view(), name="me"),
] + router.urls
