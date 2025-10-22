import os
from django.core.management.base import BaseCommand
from Segment.models import MRI_Masks, Patients

class Command(BaseCommand):
    help = "Load existing MRI files from disk into the database"

    def handle(self, *args, **options):
        base_dir = 'media/MRIs/'  

        for patient_folder in os.listdir(base_dir):
            patient_path = os.path.join(base_dir, patient_folder)

            if not os.path.isdir(patient_path):
                continue

            # Find patient in DB (if exists)
            try:
                patient = Patients.objects.get(patient_id=patient_folder)
            except Patients.DoesNotExist:
                self.stdout.write(self.style.WARNING(f"⚠️ Patient {patient_folder} not found, skipping."))
                continue

            for file_name in os.listdir(patient_path):
                if file_name.endswith(('.nii', '.nii.gz', '.dcm', '.png', '.jpg')):
                    full_path = os.path.join(patient_path, file_name)

                    patient.mri = f"MRIs/{patient_folder}/{file_name}"
                    patient.save()
                    MRI_Masks.objects.get_or_create(
                        patient=patient,
                    )

                    self.stdout.write(self.style.SUCCESS(f"✅ Added MRI for patient {patient_folder}: {file_name}"))
