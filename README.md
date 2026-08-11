# hospital-management
2. 🏥 Hospital / Patient Management System

Entities:

Patient
Doctor
Department
Appointment
Prescription
MedicalRecord
Invoice
Payment

Business rules

A doctor cannot have two appointments at the same time.
A patient cannot book overlapping appointments.
Appointment cancellation is allowed only before a certain time.
Emergency patients get priority.
Only authorized doctors can access medical records.
A prescription cannot be modified after being finalized.
Invoice can contain multiple services.
Payment cannot exceed invoice amount.
A patient's medical history must remain auditable.
Receptionist, doctor, nurse and admin have different permissions.
