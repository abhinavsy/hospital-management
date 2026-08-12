import datetime

from django.contrib.auth.models import User
from rest_framework.test import APIClient, APITestCase

from core.models import (
    Appointment,
    Department,
    Doctor,
    Hospital,
    MedicalRecord,
    Patient,
    Prescription,
    PrescriptionItem,
    UserProfile,
)
from pharmacy_app.models import Medicine


class PharmacistScopingTests(APITestCase):
    def setUp(self):
        self.hospital = Hospital.objects.create(name="Test Hospital", hospital_code="TH1")
        self.other_hospital = Hospital.objects.create(name="Other Hospital", hospital_code="OH1")

        self.department = Department.objects.create(hospital=self.hospital, name="Cardiology")
        self.doctor = Doctor.objects.create(
            department=self.department, name="Dr. A", license_number="L1",
            specialization="Cardio", phone="111", joining_date=datetime.date.today(),
        )
        self.patient = Patient.objects.create(
            patient_number="P1", first_name="John", last_name="Doe",
            date_of_birth=datetime.date(1990, 1, 1), gender="M", phone="333",
        )

        self.medicine = Medicine.objects.create(
            name="Paracetamol", category=Medicine.Category.TABLET, unit_price="5.00",
        )
        self.inactive_medicine = Medicine.objects.create(
            name="Discontinued Drug", unit_price="9.00", is_active=False,
        )

        appointment = Appointment.objects.create(
            patient=self.patient, hospital=self.hospital, doctor=self.doctor,
            appointment_date=datetime.date.today(), start_time="10:00", end_time="10:30",
        )
        record = MedicalRecord.objects.create(
            appointment=appointment, symptoms="Fever", diagnosis="Flu",
        )
        prescription = Prescription.objects.create(medical_record=record)
        self.prescribed_item = PrescriptionItem.objects.create(
            prescription=prescription, medicine=self.medicine,
            dosage="500mg", frequency="TID", duration_days=3,
        )

        # An appointment/prescription at a different hospital - must stay invisible.
        other_dept = Department.objects.create(hospital=self.other_hospital, name="Neurology")
        other_doctor = Doctor.objects.create(
            department=other_dept, name="Dr. Z", license_number="L9",
            specialization="Neuro", phone="999", joining_date=datetime.date.today(),
        )
        other_appt = Appointment.objects.create(
            patient=self.patient, hospital=self.other_hospital, doctor=other_doctor,
            appointment_date=datetime.date.today(), start_time="12:00", end_time="12:30",
        )
        other_record = MedicalRecord.objects.create(
            appointment=other_appt, symptoms="Headache", diagnosis="Migraine",
        )
        other_prescription = Prescription.objects.create(medical_record=other_record)
        PrescriptionItem.objects.create(
            prescription=other_prescription, medicine=self.medicine,
            dosage="200mg", frequency="OD", duration_days=5,
        )

        self.pharmacist_user = User.objects.create_user("pharmacist1", password="pass12345")
        UserProfile.objects.create(
            user=self.pharmacist_user, role=UserProfile.Role.PHARMACIST, hospital=self.hospital,
        )

        self.client1 = APIClient()
        self.client1.force_authenticate(user=self.pharmacist_user)

    def test_pharmacist_sees_active_medicine_catalog_with_prices(self):
        response = self.client1.get("/api/pharmacy/medicines/")
        self.assertEqual(response.status_code, 200)
        names = {m["name"]: m["unit_price"] for m in response.data["results"]}
        self.assertEqual(names, {"Paracetamol": "5.00"})  # inactive medicine excluded

    def test_pharmacist_sees_prescribed_items_for_own_hospital_only(self):
        response = self.client1.get("/api/pharmacy/prescribed-items/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data["results"]), 1)
        item = response.data["results"][0]
        self.assertEqual(item["medicine"]["name"], "Paracetamol")
        self.assertEqual(item["medicine"]["unit_price"], "5.00")
        self.assertEqual(item["patient_name"], "John Doe")
        self.assertEqual(item["doctor_name"], "Dr. A")

    def test_non_pharmacist_is_denied(self):
        doctor_user = User.objects.create_user("doctor1", password="pass12345")
        UserProfile.objects.create(user=doctor_user, role=UserProfile.Role.DOCTOR, doctor=self.doctor)
        client = APIClient()
        client.force_authenticate(user=doctor_user)
        response = client.get("/api/pharmacy/medicines/")
        self.assertEqual(response.status_code, 403)
