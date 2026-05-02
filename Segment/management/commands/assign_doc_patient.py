from django.core.management.base import BaseCommand
from Auth.models import Doctors
from Segment.models import Patients, MRI_Masks

class Command(BaseCommand):
    help = "Assign a doctor to a patient"

    def add_arguments(self, parser):
        parser.add_argument("doctor_email", type=str, help="Email of the doctor")
        parser.add_argument("patient_id", type=str, help="ID of the patient")

    def handle(self, *args, **kwargs):
        doctor_email = kwargs["doctor_email"]
        patient_id = kwargs["patient_id"]

        try:
            doctor = Doctors.objects.get(email=doctor_email)
        except Doctors.DoesNotExist:
            self.stdout.write(self.style.ERROR(f"No doctor found with email {doctor_email}"))
            return

        try:
            patients = Patients.objects.filter(patient_id = patient_id)
            for m in patients :
                masks = MRI_Masks.objects.filter(patient=m)
                for p in masks : 
                    p.doctor = doctor
                    p.save()
                    self.stdout.write(
                        self.style.SUCCESS(
                            f"Assigned Doctor {doctor.email} to Patient {m.patient_id})"
                            )
                        )
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"No patient found with ID {patient_id}, errpr {e}"))
            return
        
