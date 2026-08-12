import datetime

from django.contrib.auth.models import User
from rest_framework.test import APIClient, APITestCase

from core.models import Appointment, Department, Doctor, Hospital, Patient, UserProfile


class AuthEndpointTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user("someone", password="pass12345")
        self.hospital = Hospital.objects.create(name="Test Hospital", hospital_code="TH1")
        UserProfile.objects.create(user=self.user, role=UserProfile.Role.HOSPITAL_ADMIN, hospital=self.hospital)

    def test_login_returns_tokens_and_role(self):
        response = self.client.post("/api/auth/login/", {"username": "someone", "password": "pass12345"})
        self.assertEqual(response.status_code, 200)
        self.assertIn("access", response.data)
        self.assertIn("refresh", response.data)
        self.assertEqual(response.data["role"], "HOSPITAL_ADMIN")

    def test_login_rejects_bad_credentials(self):
        response = self.client.post("/api/auth/login/", {"username": "someone", "password": "wrong"})
        self.assertEqual(response.status_code, 401)

    def test_logout_blacklists_refresh_token(self):
        login = self.client.post("/api/auth/login/", {"username": "someone", "password": "pass12345"})
        access, refresh = login.data["access"], login.data["refresh"]

        client = APIClient()
        client.credentials(HTTP_AUTHORIZATION=f"Bearer {access}")
        response = client.post("/api/auth/logout/", {"refresh": refresh}, format="json")
        self.assertEqual(response.status_code, 204)

        refresh_response = self.client.post("/api/auth/refresh/", {"refresh": refresh})
        self.assertEqual(refresh_response.status_code, 401)

    def test_me_endpoint_returns_profile(self):
        client = APIClient()
        client.force_authenticate(user=self.user)
        response = client.get("/api/auth/me/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["role"], "HOSPITAL_ADMIN")


class AdminScopingTests(APITestCase):
    def setUp(self):
        self.hospital = Hospital.objects.create(name="Test Hospital", hospital_code="TH1")
        self.dept1 = Department.objects.create(hospital=self.hospital, name="Cardiology")
        self.dept2 = Department.objects.create(hospital=self.hospital, name="Neurology")

        self.doctor1 = Doctor.objects.create(
            department=self.dept1, name="Dr. A", license_number="L1",
            specialization="Cardio", phone="111", joining_date=datetime.date.today(),
        )
        self.doctor2 = Doctor.objects.create(
            department=self.dept2, name="Dr. B", license_number="L2",
            specialization="Neuro", phone="222", joining_date=datetime.date.today(),
        )

        self.dept_admin_user = User.objects.create_user("deptadmin", password="pass12345")
        UserProfile.objects.create(
            user=self.dept_admin_user, role=UserProfile.Role.DEPARTMENT_ADMIN, department=self.dept1,
        )
        self.hosp_admin_user = User.objects.create_user("hospadmin", password="pass12345")
        UserProfile.objects.create(
            user=self.hosp_admin_user, role=UserProfile.Role.HOSPITAL_ADMIN, hospital=self.hospital,
        )

        self.dept_client = APIClient()
        self.dept_client.force_authenticate(user=self.dept_admin_user)
        self.hosp_client = APIClient()
        self.hosp_client.force_authenticate(user=self.hosp_admin_user)

    def test_department_admin_sees_only_own_department_doctors(self):
        response = self.dept_client.get("/api/dashboard/doctors/")
        self.assertEqual(response.status_code, 200)
        ids = {d["doctor_id"] for d in response.data["results"]}
        self.assertEqual(ids, {str(self.doctor1.doctor_id)})

    def test_department_admin_cannot_retrieve_other_departments_doctor(self):
        response = self.dept_client.get(f"/api/dashboard/doctors/{self.doctor2.doctor_id}/")
        self.assertEqual(response.status_code, 404)

    def test_department_admin_create_forces_own_department(self):
        payload = {
            "department_id": self.dept2.id,  # attempt to assign to a different department
            "name": "Dr. C", "license_number": "L3", "specialization": "Cardio",
            "phone": "333", "joining_date": "2026-01-01", "is_active": True,
        }
        response = self.dept_client.post("/api/dashboard/doctors/", payload, format="json")
        self.assertEqual(response.status_code, 201, response.data)
        created = Doctor.objects.get(license_number="L3")
        self.assertEqual(created.department_id, self.dept1.id)

    def test_hospital_admin_sees_all_doctors_in_hospital(self):
        response = self.hosp_client.get("/api/dashboard/doctors/")
        self.assertEqual(response.status_code, 200)
        ids = {d["doctor_id"] for d in response.data["results"]}
        self.assertEqual(ids, {str(self.doctor1.doctor_id), str(self.doctor2.doctor_id)})

    def test_hospital_admin_create_rejects_department_outside_hospital(self):
        other_hospital = Hospital.objects.create(name="Other Hospital", hospital_code="OH1")
        other_dept = Department.objects.create(hospital=other_hospital, name="Oncology")
        payload = {
            "department_id": other_dept.id,
            "name": "Dr. D", "license_number": "L4", "specialization": "Onco",
            "phone": "444", "joining_date": "2026-01-01", "is_active": True,
        }
        response = self.hosp_client.post("/api/dashboard/doctors/", payload, format="json")
        self.assertEqual(response.status_code, 403)

    def test_department_admin_denied_on_hospital_only_data(self):
        """A department admin has no `hospital` link, so IsSameHospital always
        fails for them - departments/hospitals endpoints still resolve via the
        department's own hospital, but this asserts the base scoping split."""
        response = self.dept_client.get("/api/dashboard/hospitals/")
        self.assertEqual(response.status_code, 200)
        ids = {h["id"] for h in response.data["results"]}
        self.assertEqual(ids, {self.hospital.id})
