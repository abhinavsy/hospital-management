import datetime

from django.contrib.auth.models import User
from rest_framework.test import APIClient, APITestCase

from core.models import Appointment, Department, Doctor, Hospital, Invoice, Patient, UserProfile


class PatientScopingTests(APITestCase):
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

        self.patient1 = Patient.objects.create(
            patient_number="P1", first_name="John", last_name="Doe",
            date_of_birth=datetime.date(1990, 1, 1), gender="M", phone="333",
        )
        self.patient2 = Patient.objects.create(
            patient_number="P2", first_name="Jane", last_name="Roe",
            date_of_birth=datetime.date(1991, 1, 1), gender="F", phone="444",
        )

        self.user1 = User.objects.create_user("patient1", password="pass12345")
        UserProfile.objects.create(user=self.user1, role=UserProfile.Role.PATIENT, patient=self.patient1)
        self.user2 = User.objects.create_user("patient2", password="pass12345")
        UserProfile.objects.create(user=self.user2, role=UserProfile.Role.PATIENT, patient=self.patient2)

        self.appt1 = Appointment.objects.create(
            patient=self.patient1, hospital=self.hospital, doctor=self.doctor,
            appointment_date=datetime.date.today(), start_time="10:00", end_time="10:30",
        )
        self.appt2 = Appointment.objects.create(
            patient=self.patient2, hospital=self.hospital, doctor=self.doctor,
            appointment_date=datetime.date.today(), start_time="11:00", end_time="11:30",
        )
        self.invoice1 = Invoice.objects.create(
            patient=self.patient1, invoice_number="INV1", subtotal=100, total=100,
        )

        self.client1 = APIClient()
        self.client1.force_authenticate(user=self.user1)
        self.client2 = APIClient()
        self.client2.force_authenticate(user=self.user2)

    def test_patient_sees_own_profile(self):
        response = self.client1.get("/api/patient/me/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["patient_number"], "P1")

    def test_patient_only_sees_own_appointments(self):
        response = self.client1.get("/api/patient/appointments/")
        self.assertEqual(response.status_code, 200)
        ids = [a["id"] for a in response.data["results"]]
        self.assertEqual(ids, [self.appt1.id])

    def test_patient_cannot_retrieve_another_patients_appointment(self):
        response = self.client1.get(f"/api/patient/appointments/{self.appt2.id}/")
        self.assertEqual(response.status_code, 404)

    def test_patient_can_retrieve_own_appointment(self):
        response = self.client1.get(f"/api/patient/appointments/{self.appt1.id}/")
        self.assertEqual(response.status_code, 200)

    def test_patient_only_sees_own_invoices(self):
        response = self.client1.get("/api/patient/invoices/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data["results"]), 1)

        response2 = self.client2.get("/api/patient/invoices/")
        self.assertEqual(response2.status_code, 200)
        self.assertEqual(len(response2.data["results"]), 0)

    def test_unauthenticated_request_is_rejected(self):
        client = APIClient()
        response = client.get("/api/patient/me/")
        self.assertEqual(response.status_code, 401)
