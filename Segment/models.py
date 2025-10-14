from django.db import models

# Create your models here.
class Patient(models.Model):
    patient_id = models.CharField(max_length=100, unique=True)
    # gender = models.CharField(max_length=20, choices=['F','M'])
    

    def __str__(self):
        return self.patient_id
    
class Slice(models.Model):
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE, related_name='slices')
    title = models.CharField(max_length=255)
    image = models.ImageField(upload_to='MRIs/')

    def __str__(self):
        return self.title
    

class MRI_Mask(models.Model):
    mask_id = models.AutoField(primary_key=True)
    coordinates = models.JSONField(null=True, blank=True)  
    mask_path = models.ImageField(upload_to='Masks/', null=True, blank=True)  # saved mask image or overlay
    slice = models.ForeignKey(Slice, on_delete=models.CASCADE, related_name='masks')
    rating = models.IntegerField(null=True, blank=True)
    doctor_id = models.IntegerField(null=True, blank=True)
    rater_id = models.IntegerField(null=True, blank=True)
    structure_id = models.IntegerField(null=True, blank=True)

    def __str__(self):
        return f"Mask {self.mask_id} for {self.slice.title}"


