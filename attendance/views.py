import json
import base64
from datetime import datetime
from django.shortcuts import render, redirect
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.utils import timezone
from .models import Company, Device, Employee, AttendanceLog


def landing_view(request):
    try:
        if request.user.is_authenticated and hasattr(request.user, 'company'):
            return redirect('dashboard')
    except Exception:
        pass
    return render(request, 'landing.html')


def register_view(request):
    try:
        if request.user.is_authenticated and hasattr(request.user, 'company'):
            return redirect('dashboard')
    except Exception:
        pass

    error = None
    if request.method == 'POST':
        company_name = request.POST.get('company_name')
        username = request.POST.get('username')
        password = request.POST.get('password')
        if User.objects.filter(username=username).exists():
            error = "Bu login band, iltimos boshqa login tanlang!"
        else:
            user = User.objects.create_user(username=username, password=password)
            Company.objects.create(name=company_name, owner=user, is_active=True)
            login(request, user)
            return redirect('dashboard')
    return render(request, 'register.html', {'error': error})


def login_view(request):
    try:
        if request.user.is_authenticated and hasattr(request.user, 'company'):
            return redirect('dashboard')
    except Exception:
        pass

    error = None
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        if user is not None:
            try:
                if hasattr(user, 'company'):
                    if user.company.is_active:
                        login(request, user)
                        return redirect('dashboard')
                    else:
                        error = "Kompaniyangiz obunasi faol emas. Administrator bilan bog'laning."
                else:
                    error = "Bu foydalanuvchiga kompaniya biriktirilmagan (Super-admin /admin/ orqali kiradi)."
            except Exception as e:
                error = f"Xatolik: {str(e)}"
        else:
            error = "Login yoki parol noto'g'ri!"
    return render(request, 'login.html', {'error': error})


def logout_view(request):
    logout(request)
    return redirect('landing')


@login_required(login_url='/login/')
def dashboard_view(request):
    if not hasattr(request.user, 'company'):
        return redirect('/admin/')
    company = request.user.company

    if request.method == 'POST':
        action = request.POST.get('action')
        if action == 'add_employee':
            photo_data = None
            photo_file = request.FILES.get('photo')
            if photo_file:
                encoded = base64.b64encode(photo_file.read()).decode('utf-8')
                photo_data = f"data:{photo_file.content_type};base64,{encoded}"

            Employee.objects.create(
                company=company,
                full_name=request.POST.get('full_name'),
                device_user_id=request.POST.get('device_user_id'),
                department=request.POST.get('department', ''),
                work_start_time=request.POST.get('work_start_time', '09:00'),
                photo_base64=photo_data
            )
            return redirect('dashboard')
        elif action == 'add_device':
            Device.objects.create(
                company=company,
                name=request.POST.get('name'),
                brand=request.POST.get('brand', 'universal'),
                serial_number=request.POST.get('serial_number')
            )
            return redirect('dashboard')

    today = timezone.now().date()
    employees = Employee.objects.filter(company=company, is_active=True)
    devices = Device.objects.filter(company=company, is_active=True)
    today_logs = AttendanceLog.objects.filter(company=company, timestamp__date=today).select_related('employee', 'device')

    present_employees = {}
    late_employees = {}
    logs_data = []

    for log in today_logs:
        is_late = False
        late_minutes = 0
        if log.event_type == 'in':
            present_employees[log.employee.id] = log
            if log.timestamp.time() > log.employee.work_start_time:
                is_late = True
                t1 = datetime.combine(today, log.employee.work_start_time)
                t2 = datetime.combine(today, log.timestamp.time())
                late_minutes = int((t2 - t1).total_seconds() // 60)
                late_employees[log.employee.id] = {'employee': log.employee, 'time': log.timestamp, 'minutes': late_minutes}
        logs_data.append({'log': log, 'is_late': is_late, 'late_minutes': late_minutes})

    absent_list = [emp for emp in employees if emp.id not in present_employees]
    total_employees = employees.count()
    present_count = len(present_employees)
    late_count = len(late_employees)
    on_time_count = max(0, present_count - late_count)
    absent_count = len(absent_list)

    context = {
        'company': company,
        'today': today,
        'employees': employees,
        'devices': devices,
        'total_employees': total_employees,
        'present_count': present_count,
        'late_count': late_count,
        'on_time_count': on_time_count,
        'absent_count': absent_count,
        'absent_list': absent_list,
        'late_list': list(late_employees.values()),
        'logs_data': logs_data,
    }
    return render(request, 'dashboard.html', context)


def parse_device_payload(brand, request):
    raw_data = {}
    user_id = None
    try:
        if request.content_type == 'application/json':
            raw_data = json.loads(request.body.decode('utf-8'))
            user_id = raw_data.get('user_id') or raw_data.get('employeeNoString') or raw_data.get('UserID') or raw_data.get('pin')
        elif 'multipart/form-data' in (request.content_type or ''):
            event_log = request.POST.get('event_log')
            if event_log:
                raw_data = json.loads(event_log)
                user_id = raw_data.get('AccessControllerEvent', {}).get('employeeNoString')
            else:
                raw_data = dict(request.POST)
                user_id = request.POST.get('user_id') or request.POST.get('pin')
        else:
            body_text = request.body.decode('utf-8', errors='ignore')
            raw_data = {'raw_text': body_text}
            if 'PIN=' in body_text:
                for part in body_text.split('\t'):
                    if part.startswith('PIN='):
                        user_id = part.split('=')
    except Exception as e:
        raw_data = {'error': str(e)}
    return str(user_id).strip() if user_id else None, raw_data


@csrf_exempt
def universal_webhook(request, token):
    try:
        device = Device.objects.select_related('company').get(api_token=token, is_active=True, company__is_active=True)
    except Device.DoesNotExist:
        return JsonResponse({'status': 'error', 'message': 'Qurilma topilmadi yoki kompaniya obunasi faol emas'}, status=404)

    if request.method in ['POST', 'GET']:
        user_id, raw_data = parse_device_payload(device.brand, request)
        if not user_id:
            return JsonResponse({'status': 'ignored', 'message': 'Xodim ID si aniqlanmadi'}, status=200)

        employee = Employee.objects.filter(company=device.company, device_user_id=user_id, is_active=True).first()
        if not employee:
            return JsonResponse({'status': 'error', 'message': f'ID {user_id} li xodim bu kompaniyada topilmadi'}, status=404)

        today = timezone.now().date()
        last_log = AttendanceLog.objects.filter(company=device.company, employee=employee, timestamp__date=today).first()
        event_type = 'out' if (last_log and last_log.event_type == 'in') else 'in'

        AttendanceLog.objects.create(
            company=device.company,
            employee=employee,
            device=device,
            timestamp=timezone.now(),
            event_type=event_type,
            raw_data=raw_data
        )
        return JsonResponse({'status': 'success', 'company': device.company.name, 'employee': employee.full_name, 'event': event_type}, status=200)

    return JsonResponse({'status': 'error', 'message': 'Noto‘g‘ri so‘rov'}, status=405)
