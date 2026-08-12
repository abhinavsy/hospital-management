import datetime

from django.contrib.auth.models import User
from rest_framework.test import APIClient, APITestCase

from core.models import Appointment, Department, Doctor, Hospital, Patient, UserProfile
from pharmacy_app.models import Medicine


class DoctorScopingTests(APITestCase):
    def setUp(self):
        self.hospital = Hospital.objects.create(name="Test Hospital", hospital_code="TH1")
        self.department = Department.objects.create(hospital=self.hospital, name="Cardiology")

        self.doctor1 = Doctor.objects.create(
            department=self.department, name="Dr. A", license_number="L1",
            specialization="Cardio", phone="111", joining_date=datetime.date.today(),
        )
        self.doctor2 = Doctor.objects.create(
            department=self.department, name="Dr. B", license_number="L2",
            specialization="Cardio", phone="222", joining_date=datetime.date.today(),
        )

        self.patient = Patient.objects.create(
            patient_number="P1", first_name="John", last_name="Doe",
            date_of_birth=datetime.date(1990, 1, 1), gender="M", phone="333",
        )

        self.medicine = Medicine.objects.create(
            name="Paracetamol", category=Medicine.Category.TABLET, unit_price="5.00",
        )

        self.user1 = User.objects.create_user("doctor1", password="pass12345")
        UserProfile.objects.create(user=self.user1, role=UserProfile.Role.DOCTOR, doctor=self.doctor1)
        self.user2 = User.objects.create_user("doctor2", password="pass12345")
        UserProfile.objects.create(user=self.user2, role=UserProfile.Role.DOCTOR, doctor=self.doctor2)

        self.appt1 = Appointment.objects.create(
            patient=self.patient, hospital=self.hospital, doctor=self.doctor1,
            appointment_date=datetime.date.today(), start_time="10:00", end_time="10:30",
        )
        self.appt2 = Appointment.objects.create(
            patient=self.patient, hospital=self.hospital, doctor=self.doctor2,
            appointment_date=datetime.date.today(), start_time="11:00", end_time="11:30",
        )

        self.client1 = APIClient()
        self.client1.force_authenticate(user=self.user1)
        self.client2 = APIClient()
        self.client2.force_authenticate(user=self.user2)

    def test_doctor_only_sees_own_appointments(self):
        response = self.client1.get("/api/doctor/appointments/")
        self.assertEqual(response.status_code, 200)
        ids = [a["id"] for a in response.data["results"]]
        self.assertEqual(ids, [self.appt1.id])

    def test_doctor_cannot_access_other_doctors_appointment(self):
        response = self.client1.get(f"/api/doctor/appointments/{self.appt2.id}/")
        self.assertEqual(response.status_code, 404)

    def test_doctor_can_appoint_new_appointment(self):
        payload = {
            "patient": str(self.patient.patient_id),
            "appointment_date": "2026-09-01",
            "start_time": "09:00:00",
            "end_time": "09:30:00",
            "reason": "Follow-up",
        }
        response = self.client1.post("/api/doctor/appointments/", payload, format="json")
        self.assertEqual(response.status_code, 201, response.data)
        created = Appointment.objects.get(pk=response.data["id"])
        # doctor/hospital are server-derived, not client-writable
        self.assertEqual(created.doctor_id, self.doctor1.doctor_id)
        self.assertEqual(created.hospital_id, self.hospital.id)

    def test_doctor_can_add_medical_record_and_prescription_for_own_appointment(self):
        response = self.client1.post(
            f"/api/doctor/appointments/{self.appt1.id}/medical-record/",
            {"symptoms": "Cough", "diagnosis": "Cold", "treatment": "Rest"},
            format="json",
        )
        self.assertEqual(response.status_code, 200, response.data)

        response = self.client1.post(
            f"/api/doctor/appointments/{self.appt1.id}/prescriptions/",
            {"notes": "Take after meals", "items": [
                {"medicine_id": self.medicine.id, "dosage": "500mg", "frequency": "TID", "duration_days": 3},
            ]},
            format="json",
        )
        self.assertEqual(response.status_code, 201, response.data)

    def test_doctor_cannot_add_medical_record_for_other_doctors_appointment(self):
        response = self.client1.post(
            f"/api/doctor/appointments/{self.appt2.id}/medical-record/",
            {"symptoms": "Cough"},
            format="json",
        )
        self.assertEqual(response.status_code, 404)

    def test_doctor_only_sees_their_own_patients(self):
        response = self.client1.get("/api/doctor/patients/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data["results"]), 1)
