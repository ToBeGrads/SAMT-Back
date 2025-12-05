from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.contrib import messages
from .models import Patients, MRI_Masks, Structures
from Auth.models import Doctors


@admin.register(Structures)
class StructuresAdmin(admin.ModelAdmin):
    list_display = ('structure_id', 'structure_name', 'usage_count')
    search_fields = ('structure_name',)
    ordering = ('structure_name',)
    readonly_fields = ('structure_id',)
    
    def usage_count(self, obj):
        count = MRI_Masks.objects.filter(structure=obj).count()
        return count
    usage_count.short_description = 'Used in Masks'
    
    fieldsets = (
        ('Structure Information', {
            'fields': ('structure_id', 'structure_name')
        }),
    )


class MRIMasksInline(admin.TabularInline):
    model = MRI_Masks
    extra = 1  # Allow adding new assignments
    fields = ('doctor', 'structure', 'structure_color', 'has_mask_file', 'coordinates_count')
    readonly_fields = ('has_mask_file', 'coordinates_count')
    can_delete = True
    verbose_name = 'Doctor Assignment / Structure'
    verbose_name_plural = 'Assigned Doctors & Structures'
    
    def has_mask_file(self, obj):
        if obj and obj.pk:
            return '✓' if obj.mask_path else '✗'
        return '—'
    has_mask_file.short_description = 'Has Mask'
    
    def coordinates_count(self, obj):
        if obj and obj.pk:
            return len(obj.coordinates) if obj.coordinates else 0
        return 0
    coordinates_count.short_description = 'Coords'


@admin.register(Patients)
class PatientsAdmin(admin.ModelAdmin):
    list_display = ('patient_id', 'gender', 'birth_year', 'age_display', 
                    'view_mri_link', 'assigned_doctors_count', 'structures_count')
    list_filter = ('gender', 'birth_year')
    search_fields = ('patient_id',)
    readonly_fields = ('patient_id', 'age_display', 'mri_preview')
    inlines = [MRIMasksInline]
    
    fieldsets = (
        ('Patient Information', {
            'fields': ('patient_id', 'gender', 'birth_year', 'age_display')
        }),
        ('MRI Data', {
            'fields': ('mri', 'mri_preview', 'dims', 'modality')
        }),
    )
    
    def age_display(self, obj):
        if obj.birth_year:
            return f"{obj.age} years"
        return "—"
    age_display.short_description = 'Age'
    
    def mri_preview(self, obj):
        if obj.mri:
            return format_html(
                '<a href="{}" target="_blank">📁 View MRI File</a><br>'
                '<small>Path: {}</small>',
                obj.mri.url,
                obj.mri.name
            )
        return format_html('<span style="color: red;">No MRI uploaded</span>')
    mri_preview.short_description = 'MRI Preview'
    
    def view_mri_link(self, obj):
        if obj.mri:
            return format_html('<a href="{}" target="_blank">📁 View</a>', obj.mri.url)
        return '—'
    view_mri_link.short_description = 'MRI File'
    
    def assigned_doctors_count(self, obj):
        count = MRI_Masks.objects.filter(patient=obj).values('doctor').distinct().count()
        return count
    assigned_doctors_count.short_description = '👨‍⚕️ Doctors'
    
    def structures_count(self, obj):
        count = MRI_Masks.objects.filter(patient=obj, structure__isnull=False).count()
        return count
    structures_count.short_description = '🧠 Structures'
    
    actions = ['assign_to_doctor']
    
    def assign_to_doctor(self, request, queryset):
        """Custom action to assign selected patients to a doctor"""
        count = queryset.count()
        self.message_user(
            request,
            f'{count} patient(s) selected. To assign them to a doctor, go to MRI Masks and create new entries.',
            messages.INFO
        )
    assign_to_doctor.short_description = 'Prepare to assign to doctor'


@admin.register(MRI_Masks)
class MRIMasksAdmin(admin.ModelAdmin):
    list_display = ('mask_id', 'patient_link', 'doctor_link', 'structure_link', 
                    'color_preview', 'coordinates_info')
    list_filter = ('doctor', 'structure', 'structure_color')
    search_fields = ('patient__patient_id', 'doctor__email', 'structure__structure_name')
    readonly_fields = ('mask_id', 'mask_preview', 'coordinates_preview')
    autocomplete_fields = ['patient']
    
    fieldsets = (
        ('Assignment Information', {
            'fields': ('mask_id', 'patient', 'doctor', 'structure'),
            'description': 'Assign a patient to a doctor. Leave structure empty for initial assignment.'
        }),
        ('Structure Visualization', {
            'fields': ('structure_color',),
            'classes': ('collapse',)
        }),
        ('Coordinates', {
            'fields': ('coordinates', 'coordinates_preview'),
            'classes': ('collapse',)
        }),
        ('Mask Data', {
            'fields': ('mask_path', 'mask_preview', 'dims'),
            'classes': ('collapse',)
        }),
    )
    
    def patient_link(self, obj):
        if obj.patient:
            url = reverse('admin:Segment_patients_change', args=[obj.patient.patient_id])
            return format_html('<a href="{}">{}</a>', url, obj.patient.patient_id)
        return '—'
    patient_link.short_description = 'Patient'
    
    def doctor_link(self, obj):
        if obj.doctor:
            url = reverse('admin:Auth_doctors_change', args=[obj.doctor.id])
            return format_html('<a href="{}">{}</a>', url, obj.doctor.email)
        return '—'
    doctor_link.short_description = 'Doctor'
    
    def structure_link(self, obj):
        if obj.structure:
            url = reverse('admin:Segment_structures_change', args=[obj.structure.structure_id])
            return format_html('<a href="{}">{}</a>', url, obj.structure.structure_name)
        return format_html('<span style="color: gray;">Not assigned (Patient-Doctor link only)</span>')
    structure_link.short_description = 'Structure'
    
    def color_preview(self, obj):
        if obj.structure_color:
            return format_html(
                '<div style="width:30px;height:20px;background-color:{};border:1px solid #333;border-radius:3px;"></div>',
                obj.structure_color
            )
        return '—'
    color_preview.short_description = 'Color'
    
    def mask_status(self, obj):
        if obj.mask_path:
            return format_html('<span style="color: green;">✓ Uploaded</span>')
        return format_html('<span style="color: orange;">⚠ Not uploaded</span>')
    mask_status.short_description = 'Mask Status'
    
    def coordinates_info(self, obj):
        if obj.coordinates:
            count = len(obj.coordinates)
            segmented = sum(1 for c in obj.coordinates if c.get('hasSegmentation', False))
            return format_html('{} coords<br><small>({} segmented)</small>', count, segmented)
        return '0'
    coordinates_info.short_description = 'Coordinates'
    
    def mask_preview(self, obj):
        if obj.mask_path:
            return format_html(
                '<a href="{}" target="_blank">📄 Download Mask</a><br>'
                '<small>Path: {}</small>',
                obj.mask_path.url,
                obj.mask_path.name
            )
        return format_html('<span style="color: gray;">No mask uploaded yet</span>')
    mask_preview.short_description = 'Mask File'
    
    def coordinates_preview(self, obj):
        if obj.coordinates:
            preview = '<table style="border-collapse: collapse; font-size: 11px; width: 100%;">'
            preview += '<tr style="background: #f0f0f0;"><th>X</th><th>Y</th><th>Z</th><th>Orientation</th><th>Segmented</th></tr>'
            for coord in obj.coordinates[:10]:
                seg_icon = '✓' if coord.get('hasSegmentation', False) else '✗'
                preview += f'''<tr>
                    <td style="padding: 2px 5px;">{coord.get("x", "—")}</td>
                    <td style="padding: 2px 5px;">{coord.get("y", "—")}</td>
                    <td style="padding: 2px 5px;">{coord.get("z", "—")}</td>
                    <td style="padding: 2px 5px;">{coord.get("orientation", "—")}</td>
                    <td style="padding: 2px 5px;">{seg_icon}</td>
                </tr>'''
            if len(obj.coordinates) > 10:
                preview += f'<tr><td colspan="5" style="padding: 5px; text-align: center; font-style: italic;">... and {len(obj.coordinates) - 10} more</td></tr>'
            preview += '</table>'
            return format_html(preview)
        return 'No coordinates'
    coordinates_preview.short_description = 'Coordinates Data'
    
    def save_model(self, request, obj, form, change):
        """Custom save to handle initial patient-doctor assignments"""
        super().save_model(request, obj, form, change)
        
        # If this is a new assignment without structure, notify
        if not change and not obj.structure:
            self.message_user(
                request,
                f'Patient {obj.patient.patient_id} assigned to Dr. {obj.doctor.email}. '
                f'Doctor can now add structures through the frontend.',
                messages.SUCCESS
            )


# Customize admin site
admin.site.site_header = 'SAMT Medical Imaging Administration'
admin.site.site_title = 'SAMT Admin'
admin.site.index_title = 'Medical Data Management'