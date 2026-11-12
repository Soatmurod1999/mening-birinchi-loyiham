from django.contrib import admin
from .models import Device, Employee, AttendanceLog

@admin.register(Device)
class DeviceAdmin(admin.ModelAdmin):
    list_display = ('name', 'brand', 'serial_number', 'webhook_url', 'is_active')
    readonly_fields = ('api_token', 'webhook_url')

    def webhook_url(self, obj):
        return f"/api/webhook/{obj.api_token}/"
    webhook_url.short_description = "Qurilmaga kiritiladigan Webhook manzili"

@admin.register(Employee)
class EmployeeAdmin(admin.ModelAdmin):
    list_display = ('full_name', 'device_user_id', 'department', 'work_start_time', 'is_active')
    search_fields = ('full_name', 'device_user_id')

@admin.register(AttendanceLog)
class AttendanceLogAdmin(admin.ModelAdmin):
    list_display = ('employee', 'device', 'timestamp', 'event_type')
    list_filter = ('device', 'event_type', 'timestamp')
    readonly_fields = ('raw_data',)
