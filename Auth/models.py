from django.contrib.auth.models import AbstractBaseUser, BaseUserManager
from django.db import models

class DoctorManager(BaseUserManager):
    def create_user(self, email, password=None):
        if not email:
            raise ValueError("Email is required")
        user = self.model(email=self.normalize_email(email))
        user.set_password(password)
        user.save(using=self._db)
        return user

class Doctors(AbstractBaseUser):
    email = models.EmailField(unique=True)
    USERNAME_FIELD = 'email'
    objects = DoctorManager()
