import os
from django.core.management.base import BaseCommand
from django.conf import settings
from MRI.models import Patient, Slice


class Command(BaseCommand):
    help = 'Loads MRI slices grouped by patient folders into the database'

    def handle(self, *args, **options):
        base_path = os.path.join(settings.MEDIA_ROOT, 'MRIs')

        if not os.path.exists(base_path):
            self.stderr.write(self.style.ERROR(f" Path not found: {base_path}"))
            return

        total_patients = 0
        total_slices = 0

        for patient_folder in os.listdir(base_path):
            patient_path = os.path.join(base_path, patient_folder)

            if not os.path.isdir(patient_path):
                continue  # skip non-folder files

            # Create or get patient
            patient, created = Patient.objects.get_or_create(patient_id=patient_folder)
            if created:
                total_patients += 1

            # Load slices
            for filename in os.listdir(patient_path):
                if filename.lower().endswith(('.png', '.jpg', '.jpeg', '.tiff')):
                    relative_path = f'MRIs/{patient_folder}/{filename}'
                    title = os.path.splitext(filename)[0]

                    if not Slice.objects.filter(image=relative_path).exists():
                        Slice.objects.create(
                            patient=patient,
                            title=title,
                            image=relative_path
                        )
                        total_slices += 1

        self.stdout.write(self.style.SUCCESS(
            f" Done! Added {total_patients} patients and {total_slices} slices."
        ))
