import csv
from django.core.management.base import BaseCommand
from Segment.models import Patients

class Command(BaseCommand):
    help = 'Load patients with only birth year into the database'

    def handle(self, *args, **options):
        file_path = 'assets/patients.csv'

        with open(file_path, newline='', encoding='utf-8') as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                raw_date = row.get('birth_date', '').strip()

                birth_year = None
                if raw_date:
                    # Try to extract a valid year
                    for sep in ['/', '-', '.']:
                        parts = raw_date.split(sep)
                        if len(parts) > 0 and parts[0].isdigit() and len(parts[0]) == 4:
                            birth_year = int(parts[0])
                            break
                        elif len(parts) > 2 and parts[2].isdigit() and len(parts[2]) == 4:
                            birth_year = int(parts[2])
                            break

                    # Skip nonsense years like 0000 or 9999
                    if birth_year and (birth_year < 1900 or birth_year > 2025):
                        birth_year = None

                if not birth_year:
                    self.stdout.write(
                        self.style.WARNING(f"No valid year for patient {row['Patient ID']}, storing NULL")
                    )

                Patients.objects.update_or_create(
                    patient_id=row['Patient ID'],
                    defaults={
                        'gender': row.get('Sex', 'Unknown'),
                        'birth_year': birth_year,
                    }
                )

        self.stdout.write(self.style.SUCCESS('Patients imported successfully with birth years!'))
