from rest_framework import viewsets
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.views import TokenObtainPairView

from core.models import Appointment, Department, Doctor, Hospital, Invoice, Patient
from core.permissions import (
    IsDepartmentAdmin,
    IsHospitalAdmin,
    IsSameDepartment,
    IsSameHospital,
)
from core.serializers import (
    AppointmentSerializer,
    DepartmentSerializer,
    DoctorSerializer,
    HospitalSerializer,
    InvoiceSerializer,
    PatientSerializer,
    UserProfileSerializer,
)


class LoginView(TokenObtainPairView):
    """POST {username, password} -> {access, refresh, role, ...}.

    Wraps SimpleJWT's standard obtain-pair view so the response also
    surfaces the caller's role and linked-object summary, saving the
    client an extra round trip to /auth/me/ right after logging in.
    """

    permission_classes = [AllowAny]

    def post(self, request, *args, **kwargs):
        response = super().post(request, *args, **kwargs)
        if response.status_code == 200:
            username = request.data.get("username")
            from django.contrib.auth.models import User

            user = User.objects.filter(username=username).first()
            profile = getattr(user, "profile", None) if user else None
            response.data["role"] = profile.role if profile else None
        return response


class LogoutView(APIView):
    """POST {refresh} -> blacklists the refresh token so it can no longer be used."""

    permission_classes = [IsAuthenticated]

    def post(self, request):
        refresh = request.data.get("refresh")
        if not refresh:
            return Response({"detail": "refresh token is required."}, status=400)
        try:
            RefreshToken(refresh).blacklist()
        except Exception:
            return Response({"detail": "Invalid or already-blacklisted token."}, status=400)
        return Response(status=204)


class MeView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        profile = getattr(request.user, "profile", None)
        if profile is None:
            return Response({"detail": "No profile is linked to this account."}, status=404)
        return Response(UserProfileSerializer(profile).data)


class _AdminScopedMixin:
    """Shared queryset-scoping for the department-admin / hospital-admin surface.

    Both roles are allowed on these viewsets; `IsSameDepartment` short-circuits
    to False for a hospital admin (no profile.department_id) and vice versa,
    so the `|` composition only ever succeeds via the branch matching the
    caller's actual role.
    """

    permission_classes = [
        IsDepartmentAdmin | IsHospitalAdmin,
        IsSameDepartment | IsSameHospital,
    ]

    def _profile(self):
        return self.request.user.profile


class DoctorViewSet(_AdminScopedMixin, viewsets.ModelViewSet):
    serializer_class = DoctorSerializer

    def get_queryset(self):
        profile = self._profile()
        if profile.role == profile.Role.DEPARTMENT_ADMIN:
            return Doctor.objects.filter(department=profile.department)
        return Doctor.objects.filter(department__hospital=profile.hospital)

    def perform_create(self, serializer):
        profile = self._profile()
        if profile.role == profile.Role.DEPARTMENT_ADMIN:
            serializer.save(department=profile.department)
        else:
            department = serializer.validated_data["department"]
            if department.hospital_id != profile.hospital_id:
                from rest_framework.exceptions import PermissionDenied

                raise PermissionDenied("That department is not part of your hospital.")
            serializer.save()

    def perform_update(self, serializer):
        self.perform_create(serializer)


class DepartmentViewSet(_AdminScopedMixin, viewsets.ReadOnlyModelViewSet):
    serializer_class = DepartmentSerializer

    def get_queryset(self):
        profile = self._profile()
        if profile.role == profile.Role.DEPARTMENT_ADMIN:
            return Department.objects.filter(pk=profile.department_id)
        return Department.objects.filter(hospital=profile.hospital)


class HospitalViewSet(_AdminScopedMixin, viewsets.ReadOnlyModelViewSet):
    serializer_class = HospitalSerializer

    def get_queryset(self):
        profile = self._profile()
        hospital_id = (
            profile.department.hospital_id
            if profile.role == profile.Role.DEPARTMENT_ADMIN
            else profile.hospital_id
        )
        return Hospital.objects.filter(pk=hospital_id)


class PatientViewSet(_AdminScopedMixin, viewsets.ReadOnlyModelViewSet):
    serializer_class = PatientSerializer

    def get_queryset(self):
        profile = self._profile()
        if profile.role == profile.Role.DEPARTMENT_ADMIN:
            return Patient.objects.filter(
                appointments__doctor__department=profile.department
            ).distinct()
        return Patient.objects.filter(hospitals=profile.hospital).distinct()


class AppointmentViewSet(_AdminScopedMixin, viewsets.ReadOnlyModelViewSet):
    serializer_class = AppointmentSerializer

    def get_queryset(self):
        profile = self._profile()
        if profile.role == profile.Role.DEPARTMENT_ADMIN:
            return Appointment.objects.filter(doctor__department=profile.department)
        return Appointment.objects.filter(hospital=profile.hospital)


class InvoiceViewSet(_AdminScopedMixin, viewsets.ReadOnlyModelViewSet):
    """Scoped via the patient's hospital/department registration - see the
    caveat in core/permissions.py: Invoice has no direct Hospital FK, so a
    patient registered at multiple hospitals may show an invoice to more
    than one hospital admin. Acceptable for now, flagged for a future
    schema fix (Invoice.hospital)."""

    serializer_class = InvoiceSerializer

    def get_queryset(self):
        profile = self._profile()
        if profile.role == profile.Role.DEPARTMENT_ADMIN:
            return Invoice.objects.filter(
                patient__appointments__doctor__department=profile.department
            ).distinct()
        return Invoice.objects.filter(patient__hospitals=profile.hospital).distinct()
