from rest_framework.routers import DefaultRouter

from doctor_app.views import MyAppointmentViewSet, MyPatientViewSet

app_name = "doctor_app"

router = DefaultRouter()
router.register("appointments", MyAppointmentViewSet, basename="my-appointment")
router.register("patients", MyPatientViewSet, basename="my-patient")

urlpatterns = router.urls
