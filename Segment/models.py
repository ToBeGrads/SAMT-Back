from django.db import models
from datetime import date
from Auth.models import Doctors
# Create your models here.
class Structures(models.Model) : 
    structure_id = models.AutoField(max_length=255,primary_key=True)
    structure_name = models.CharField(max_length=255)
    


class Patients(models.Model):
    patient_id = models.CharField(max_length=20,primary_key=True)
    gender = models.CharField(max_length=20, choices=[('Female','F'),("Male",'M')])
    birth_year = models.IntegerField(null=True, blank=True)
    mri = models.ImageField(upload_to='MRIs/')
    status = models.CharField(max_length=20, choices=[('Finished','F'),("Unfinished",'U')])

    @property
    def age(self):
        today = date.today()
        return today.year - self.birth_year
    
    def __str__(self):
        return self.patient_id

class MRI_Masks(models.Model):
    mask_id = models.AutoField(primary_key = True)
    structure = models.ForeignKey(Structures, on_delete = models.CASCADE, null = True, blank = True)
    structure_color = models.CharField(max_length=255)
    coordinates = models.JSONField(default = list, null=True, blank=True)
    patient = models.ForeignKey(Patients, on_delete = models.CASCADE)
    doctor = models.ForeignKey(Doctors, on_delete = models.CASCADE, null = True, blank = True)
    rater = models.IntegerField(null = True, blank = True)
    mask_path = models.ImageField(upload_to = 'Masks/', null = True, blank = True)  # saved mask image or overlay
    

class MRI_MASK_Meta_Data(models.Model): 
    meta_data_id = models.AutoField(primary_key = True)
    mri_mask_id = models.ForeignKey(MRI_Masks, on_delete = models.CASCADE)
    Reading = models.CharField(choices=[('Axial','A'),('Coronal','C'),('Saggital','S')])
    Rating = models.IntegerField(max_length = 4)
    Annotators_num = models.IntegerField()