from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.models import User

from core.models import (
    Appointment,
    Department,
    Doctor,
    Hospital,
    Invoice,
    InvoiceItem,
    MedicalRecord,
    Patient,
    PatientHospital,
    Payment,
    Prescription,
    PrescriptionItem,
    UserProfile,
)


class UserProfileInline(admin.StackedInline):
    model = UserProfile
    can_delete = False
    autocomplete_fields = ["patient", "doctor", "department", "hospital"]


class CustomUserAdmin(UserAdmin):
    """Lets a superuser assign a role + link the domain object (patient/doctor/
    department/hospital) to a new login account in one place, since there is
    no self-service signup flow."""

    inlines = [UserProfileInline]


admin.site.unregister(User)
admin.site.register(User, CustomUserAdmin)


@admin.register(Hospital)
class HospitalAdmin(admin.ModelAdmin):
    search_fields = ["name", "hospital_code"]


@admin.register(Department)
class DepartmentAdmin(admin.ModelAdmin):
    list_display = ["name", "hospital"]
    list_filter = ["hospital"]
    search_fields = ["name"]


@admin.register(Doctor)
class DoctorAdmin(admin.ModelAdmin):
    list_display = ["name", "department", "specialization", "is_active"]
    list_filter = ["department", "is_active"]
    search_fields = ["name", "license_number"]


@admin.register(Patient)
class PatientAdmin(admin.ModelAdmin):
    list_display = ["patient_number", "first_name", "last_name", "phone"]
    search_fields = ["patient_number", "first_name", "last_name"]


admin.site.register(PatientHospital)
admin.site.register(Appointment)
admin.site.register(MedicalRecord)
admin.site.register(Prescription)
admin.site.register(PrescriptionItem)
admin.site.register(Invoice)
admin.site.register(InvoiceItem)
admin.site.register(Payment)


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ["user", "role", "patient", "doctor", "department", "hospital"]
    list_filter = ["role"]
    autocomplete_fields = ["patient", "doctor", "department", "hospital"]
