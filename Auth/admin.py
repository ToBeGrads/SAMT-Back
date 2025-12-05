from django.contrib import admin
from django.contrib.auth.hashers import make_password
from django.utils.html import format_html
from django import forms
from .models import Doctors
from Segment.models import MRI_Masks


class AssignedPatientsInline(admin.TabularInline):
    model = MRI_Masks
    extra = 0
    fields = ('patient', 'structure', 'structure_color', 'mask_status')
    readonly_fields = ('patient', 'mask_status')
    can_delete = True
    verbose_name = 'Assigned Patient'
    verbose_name_plural = 'Assigned Patients'
    
    def mask_status(self, obj):
        if obj.mask_path:
            return '✓ Has mask'
        return '✗ No mask'
    mask_status.short_description = 'Mask'


class DoctorAdminForm(forms.ModelForm):
    password = forms.CharField(
        widget=forms.PasswordInput,
        required=False,
        help_text="Leave blank if you don't want to change the password"
    )
    
    class Meta:
        model = Doctors
        fields = ['email', 'password']
    
    def save(self, commit=True):
        doctor = super().save(commit=False)
        password = self.cleaned_data.get('password')
        
        if password:
            doctor.password = make_password(password)
        elif not doctor.pk:
            # New doctor without password
            raise forms.ValidationError("Password is required for new doctors")
            
        if commit:
            doctor.save()
        return doctor


@admin.register(Doctors)
class DoctorsAdmin(admin.ModelAdmin):
    form = DoctorAdminForm
    list_display = ('id', 'email', 'assigned_patients_display', 'total_structures', 'last_login')
    list_filter = ('last_login',)
    search_fields = ('email',)
    ordering = ('-id',)
    inlines = [AssignedPatientsInline]
    readonly_fields = ('id', 'last_login')
    
    fieldsets = (
        ('Doctor Information', {
            'fields': ('id', 'email', 'password', 'last_login')
        }),
    )
    
    def assigned_patients_display(self, obj):
        count = MRI_Masks.objects.filter(doctor=obj).values('patient').distinct().count()
        return format_html('<strong>{}</strong> patients', count)
    assigned_patients_display.short_description = '👤 Assigned Patients'
    
    def total_structures(self, obj):
        count = MRI_Masks.objects.filter(doctor=obj, structure__isnull=False).count()
        return format_html('<strong>{}</strong> structures', count)
    total_structures.short_description = '🧠 Structures'