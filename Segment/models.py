from django.db import models
from Auth.models import Doctors
from datetime import date

class Patients(models.Model):
    id = models.AutoField(primary_key = True)
    patient_id = models.CharField(max_length=20)
    gender = models.CharField(max_length=20, choices=[('Female','F'),("Male",'M')])
    birth_year = models.IntegerField(null=True, blank=True)
    mri = models.FileField(upload_to='MRIs/')
    dims = models.JSONField(default = list, null=True, blank=True)
    modality = models.CharField(max_length=255, null=True)
    tag = models.CharField(max_length=25, null=True)
    # dis
    @property
    def age(self):
        today = date.today()
        return date.today().year - self.birth_year if self.birth_year else 0
    
    def __str__(self):
        return self.patient_id


# Brain structures table
class Structures(models.Model) : 
    structure_id = models.AutoField(max_length=255,primary_key=True)
    structure_name = models.CharField(max_length=255)

class MRI_Masks(models.Model):
    mask_id = models.AutoField(primary_key = True)
    structure = models.ForeignKey(Structures, on_delete = models.CASCADE, null = True, blank = True)
    structure_color = models.CharField(max_length=255, null=True, blank=True)
    coordinates = models.JSONField(default = list, null=True, blank=True)
    patient = models.ForeignKey(Patients, on_delete = models.CASCADE)
    doctor = models.ForeignKey(Doctors, on_delete = models.CASCADE, null = True, blank = True)
    rater = models.IntegerField(null = True, blank = True)
    mask_path = models.FileField(upload_to = 'Masks/', null = True, blank = True) 
    dims = models.JSONField(default = list, null=True, blank=True)
    last_modified = models.DateTimeField(auto_now=True)

