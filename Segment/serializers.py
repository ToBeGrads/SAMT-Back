from rest_framework import serializers
from .models import  MRI_Masks

class MRIMASKSSerializer(serializers.ModelSerializer):
    class Meta:
        model = MRI_Masks
        fields = ['mask_id','structure_id', 'patient_id', 'doctor_id','rater_id','mask_path']
