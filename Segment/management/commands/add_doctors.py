from django.core.management.base import BaseCommand
from Auth.models import Doctors
from django.contrib.auth.hashers import make_password

class Command(BaseCommand):
    help = "Add a doctor to the database"

    def add_arguments(self, parser):
        parser.add_argument("email", type=str, help="Doctor's email")
        parser.add_argument("password", type=str, help="Doctor's password")

    def handle(self, *args, **kwargs):
        email = kwargs["email"]
        password = kwargs["password"]
        

        # hash password 
        hashed_pw = make_password(password)
        doctor, created = Doctors.objects.get_or_create(
            email=email, 
            defaults={
                "password": hashed_pw        
                }
                )


        if created:
            self.stdout.write(self.style.SUCCESS(f"Doctor created: ({doctor.email})"))
        else:
            self.stdout.write(self.style.WARNING("Doctor with this email already exists."))
