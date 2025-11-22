import csv
from django.core.management.base import BaseCommand
from Segment.models import Structures

class Command(BaseCommand):
    help = "Load structures from CSV"

    def add_arguments(self, parser):
        parser.add_argument(
            "--file",
            type=str,
            required=True,
            help="Path to the CSV file containing structures"
        )

    def handle(self, *args, **options):
        csv_path = options["file"]

        try:
            with open(csv_path, newline="", encoding="utf-8") as csvfile:
                reader = csv.DictReader(csvfile)

                for row in reader:
                    title = row.get("title")

                    # Insert or update
                    struct, created = Structures.objects.update_or_create(
                        structure_name=title,
                    )

                    if created:
                        self.stdout.write(self.style.SUCCESS(f"Created: {title}"))
                    else:
                        self.stdout.write(self.style.WARNING(f"Updated: {title}"))

            self.stdout.write(self.style.SUCCESS("Structures imported successfully!"))

        except FileNotFoundError:
            self.stdout.write(self.style.ERROR(f"File not found: {csv_path}"))
