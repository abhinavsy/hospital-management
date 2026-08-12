"""
Role + object-level scoping for the hospital DRF API.

Every user with an account has a `core.models.UserProfile` with a `role`
and, depending on the role, a link to the specific domain object they act
as (`patient`, `doctor`, `department`, or `hospital`). That link is the
single source of truth for both:

  * queryset filtering (`get_queryset()` in each view) - so `list` never
    leaks rows and `retrieve`/`update`/`delete` on an out-of-scope pk
    404s rather than 403 (deliberate: don't confirm another tenant's
    object even exists).
  * object-level permission checks below (defense in depth for any
    view/action that fetches an object without going through a scoped
    `get_queryset()`).
"""

from rest_framework.permissions import BasePermission

from core.models import (
    Appointment,
    Department,
    Doctor,
    Hospital,
    Invoice,
    MedicalRecord,
    Patient,
    Prescription,
    PrescriptionItem,
    UserProfile,
)


def get_profile(user):
    return getattr(user, "profile", None)


def resolve_hospital(obj):
    """Best-effort single-hospital resolution for object-level hospital scoping."""
    if isinstance(obj, Hospital):
        return obj
    if isinstance(obj, Department):
        return obj.hospital
    if isinstance(obj, Doctor):
        return obj.department.hospital
    if isinstance(obj, Appointment):
        return obj.hospital
    if isinstance(obj, MedicalRecord):
        return obj.appointment.hospital
    if isinstance(obj, Prescription):
        return obj.medical_record.appointment.hospital
    if isinstance(obj, PrescriptionItem):
        return obj.prescription.medical_record.appointment.hospital
    return None


def resolve_department(obj):
    if isinstance(obj, Department):
        return obj
    if isinstance(obj, Doctor):
        return obj.department
    if isinstance(obj, Appointment):
        return obj.doctor.department
    if isinstance(obj, MedicalRecord):
        return obj.appointment.doctor.department
    if isinstance(obj, Prescription):
        return obj.medical_record.appointment.doctor.department
    if isinstance(obj, PrescriptionItem):
        return obj.prescription.medical_record.appointment.doctor.department
    return None


def patient_in_hospital(patient, hospital):
    return patient.hospitals.filter(pk=hospital.pk).exists()


def patient_in_department(patient, department):
    return Appointment.objects.filter(
        patient=patient, doctor__department=department
    ).exists()


class _RoleRequired(BasePermission):
    allowed_role = None

    def has_permission(self, request, view):
        profile = get_profile(request.user)
        return bool(profile and profile.role == self.allowed_role)


class IsPatientUser(_RoleRequired):
    allowed_role = UserProfile.Role.PATIENT

    def has_permission(self, request, view):
        return (
            super().has_permission(request, view)
            and request.user.profile.patient_id is not None
        )


class IsDoctorUser(_RoleRequired):
    allowed_role = UserProfile.Role.DOCTOR

    def has_permission(self, request, view):
        return (
            super().has_permission(request, view)
            and request.user.profile.doctor_id is not None
        )


class IsDepartmentAdmin(_RoleRequired):
    allowed_role = UserProfile.Role.DEPARTMENT_ADMIN

    def has_permission(self, request, view):
        return (
            super().has_permission(request, view)
            and request.user.profile.department_id is not None
        )


class IsHospitalAdmin(_RoleRequired):
    allowed_role = UserProfile.Role.HOSPITAL_ADMIN

    def has_permission(self, request, view):
        return (
            super().has_permission(request, view)
            and request.user.profile.hospital_id is not None
        )


class IsPharmacistUser(_RoleRequired):
    allowed_role = UserProfile.Role.PHARMACIST

    def has_permission(self, request, view):
        return (
            super().has_permission(request, view)
            and request.user.profile.hospital_id is not None
        )


class IsOwnAppointmentDoctor(BasePermission):
    """Object-level check: the appointment (or a child of it) belongs to this doctor."""

    def has_object_permission(self, request, view, obj):
        profile = get_profile(request.user)
        appointment = obj if isinstance(obj, Appointment) else getattr(obj, "appointment", None)
        return bool(
            profile
            and profile.doctor_id
            and appointment
            and appointment.doctor_id == profile.doctor_id
        )


class IsOwnPatientRecord(BasePermission):
    """Object-level check: the record (or its patient) belongs to this patient."""

    def has_object_permission(self, request, view, obj):
        profile = get_profile(request.user)
        if not (profile and profile.patient_id):
            return False
        patient = (
            obj
            if isinstance(obj, Patient)
            else getattr(obj, "patient", None)
            or getattr(getattr(obj, "appointment", None), "patient", None)
        )
        return bool(patient and patient.pk == profile.patient_id)


class IsSameDepartment(BasePermission):
    def has_object_permission(self, request, view, obj):
        profile = get_profile(request.user)
        if not (profile and profile.department_id):
            return False
        dept = resolve_department(obj)
        if dept is not None:
            return dept.pk == profile.department_id
        if isinstance(obj, Patient):
            return patient_in_department(obj, profile.department)
        if isinstance(obj, Invoice):
            return patient_in_department(obj.patient, profile.department)
        return False


class IsSameHospital(BasePermission):
    def has_object_permission(self, request, view, obj):
        profile = get_profile(request.user)
        if not (profile and profile.hospital_id):
            return False
        hospital = resolve_hospital(obj)
        if hospital is not None:
            return hospital.pk == profile.hospital_id
        if isinstance(obj, Patient):
            return patient_in_hospital(obj, profile.hospital)
        if isinstance(obj, Invoice):
            return patient_in_hospital(obj.patient, profile.hospital)
        return False
