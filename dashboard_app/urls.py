from django.urls import include, path
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import TokenRefreshView

from dashboard_app.views import (
    AppointmentViewSet,
    DepartmentViewSet,
    DoctorViewSet,
    HospitalViewSet,
    InvoiceViewSet,
    LoginView,
    LogoutView,
    MeView,
    PatientViewSet,
)

app_name = "dashboard_app"

router = DefaultRouter()
router.register("doctors", DoctorViewSet, basename="doctor")
router.register("departments", DepartmentViewSet, basename="department")
router.register("hospitals", HospitalViewSet, basename="hospital")
router.register("patients", PatientViewSet, basename="admin-patient")
router.register("appointments", AppointmentViewSet, basename="admin-appointment")
router.register("invoices", InvoiceViewSet, basename="admin-invoice")

urlpatterns = [
    path("auth/login/", LoginView.as_view(), name="login"),
    path("auth/refresh/", TokenRefreshView.as_view(), name="refresh"),
    path("auth/logout/", LogoutView.as_view(), name="logout"),
    path("auth/me/", MeView.as_view(), name="me"),
    path("dashboard/", include(router.urls)),
]
