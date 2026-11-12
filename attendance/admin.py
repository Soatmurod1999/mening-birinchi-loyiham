from django.contrib import admin
from .models import Company, Device, Employee, AttendanceLog

@admin.register(Company)
class CompanyAdmin(admin.ModelAdmin):
    list_display = ('name', 'owner', 'is_active', 'created_at')
    list_filter = ('is_active',)

@admin.register(Device)
class DeviceAdmin(admin.ModelAdmin):
    list_display = ('name', 'company', 'brand', 'webhook_url', 'is_active')
    readonly_fields = ('api_token', 'webhook_url')

    def webhook_url(self, obj):
        return f"/api/webhook/{obj.api_token}/"

@admin.register(Employee)
class EmployeeAdmin(admin.ModelAdmin):
    list_display = ('full_name', 'company', 'device_user_id', 'department', 'is_active')
    list_filter = ('company',)

@admin.register(AttendanceLog)
class AttendanceLogAdmin(admin.ModelAdmin):
    list_display = ('employee', 'company', 'timestamp', 'event_type')
    list_filter = ('company', 'event_type')
