import uuid
from django.db import models
from django.contrib.auth.models import User

class Company(models.Model):
    name = models.CharField(max_length=150, verbose_name="Kompaniya nomi")
    owner = models.OneToOneField(User, on_delete=models.CASCADE, related_name='company', verbose_name="Kompaniya rahbari (Login)")
    is_active = models.BooleanField(default=True, verbose_name="Obuna faolmi (To'lov qilinganmi)")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Qo'shilgan sana")

    def __str__(self):
        return self.name


class Device(models.Model):
    BRAND_CHOICES = [
        ('hikvision', 'Hikvision'),
        ('dahua', 'Dahua'),
        ('zkteco', 'ZKTeco'),
        ('universal', 'Boshqa / Universal API'),
    ]
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='devices', verbose_name="Kompaniya")
    name = models.CharField(max_length=100, verbose_name="Qurilma nomi")
    brand = models.CharField(max_length=20, choices=BRAND_CHOICES, default='universal', verbose_name="Brendi")
    serial_number = models.CharField(max_length=100, unique=True, verbose_name="Seriya raqami")
    api_token = models.UUIDField(default=uuid.uuid4, editable=False, unique=True, verbose_name="Webhook Token")
    is_active = models.BooleanField(default=True, verbose_name="Faolmi")

    def __str__(self):
        return f"{self.company.name} — {self.name}"


class Employee(models.Model):
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='employees', verbose_name="Kompaniya")
    full_name = models.CharField(max_length=150, verbose_name="F.I.O")
    device_user_id = models.CharField(max_length=50, verbose_name="Qurilmadagi ID raqami")
    department = models.CharField(max_length=100, blank=True, verbose_name="Bo'lim / Lavozim")
    work_start_time = models.TimeField(default="09:00:00", verbose_name="Ish boshlanish vaqti")
    is_active = models.BooleanField(default=True, verbose_name="Ishlayaptimi")

    class Meta:
        unique_together = ('company', 'device_user_id')

    def __str__(self):
        return f"{self.full_name} ({self.company.name})"


class AttendanceLog(models.Model):
    EVENT_TYPES = [
        ('in', 'Kirish'),
        ('out', 'Chiqish'),
    ]
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='logs', verbose_name="Kompaniya")
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE, related_name='logs', verbose_name="Xodim")
    device = models.ForeignKey(Device, on_delete=models.SET_NULL, null=True, verbose_name="Qurilma")
    timestamp = models.DateTimeField(verbose_name="Sana va vaqt")
    event_type = models.CharField(max_length=10, choices=EVENT_TYPES, default='in', verbose_name="Harakat turi")
    raw_data = models.JSONField(blank=True, null=True, verbose_name="Asl ma'lumot")

    class Meta:
        ordering = ['-timestamp']
