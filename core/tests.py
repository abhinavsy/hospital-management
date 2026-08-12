import datetime

from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.test import TestCase

from core.models import Department, Doctor, Hospital, Patient, UserProfile


class UserProfileValidationTests(TestCase):
    def setUp(self):
        self.hospital = Hospital.objects.create(name="Test Hospital", hospital_code="TH1")
        self.department = Department.objects.create(hospital=self.hospital, name="Cardiology")
        self.doctor = Doctor.objects.create(
            department=self.department,
            name="Dr. A",
            license_number="L1",
            specialization="Cardio",
            phone="111",
            joining_date=datetime.date.today(),
        )
        self.patient = Patient.objects.create(
            patient_number="P1",
            first_name="John",
            last_name="Doe",
            date_of_birth=datetime.date(1990, 1, 1),
            gender="M",
            phone="333",
        )

    def test_patient_role_requires_patient_link(self):
        user = User.objects.create_user("nopatient", password="pass12345")
        profile = UserProfile(user=user, role=UserProfile.Role.PATIENT)
        with self.assertRaises(ValidationError):
            profile.clean()

    def test_doctor_role_requires_doctor_link(self):
        user = User.objects.create_user("nodoctor", password="pass12345")
        profile = UserProfile(user=user, role=UserProfile.Role.DOCTOR)
        with self.assertRaises(ValidationError):
            profile.clean()

    def test_valid_profile_passes_clean(self):
        user = User.objects.create_user("patientuser", password="pass12345")
        profile = UserProfile(user=user, role=UserProfile.Role.PATIENT, patient=self.patient)
        profile.clean()  # should not raise

    def test_department_admin_requires_department(self):
        user = User.objects.create_user("deptuser", password="pass12345")
        profile = UserProfile(user=user, role=UserProfile.Role.DEPARTMENT_ADMIN)
        with self.assertRaises(ValidationError):
            profile.clean()

    def test_hospital_admin_requires_hospital(self):
        user = User.objects.create_user("hospuser", password="pass12345")
        profile = UserProfile(user=user, role=UserProfile.Role.HOSPITAL_ADMIN)
        with self.assertRaises(ValidationError):
            profile.clean()
