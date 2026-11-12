from django.shortcuts import render
import json
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.utils import timezone
from .models import Device, Employee, AttendanceLog

def parse_device_payload(brand, request):
    """Turli brend qurilmalaridan kelgan ma'lumotni yagona formatga o'tkazuvchi tarjimon"""
    raw_data = {}
    user_id = None

    try:
        # 1. Oddiy JSON formatda kelgan bo'lsa (Dahua, Universal API)
        if request.content_type == 'application/json':
            raw_data = json.loads(request.body.decode('utf-8'))
            user_id = (
                raw_data.get('user_id') or 
                raw_data.get('employeeNoString') or 
                raw_data.get('UserID') or
                raw_data.get('pin')
            )
        # 2. Multipart/form-data formatda kelgan bo'lsa (Hikvision ISAPI rasm bilan yuborganda)
        elif 'multipart/form-data' in (request.content_type or ''):
            event_log = request.POST.get('event_log')
            if event_log:
                raw_data = json.loads(event_log)
                access_event = raw_data.get('AccessControllerEvent', {})
                user_id = access_event.get('employeeNoString') or access_event.get('cardNo')
            else:
                raw_data = dict(request.POST)
                user_id = request.POST.get('user_id') or request.POST.get('pin')
        # 3. Oddiy matn yoki boshqa format (ZKTeco ADMS)
        else:
            body_text = request.body.decode('utf-8', errors='ignore')
            raw_data = {'raw_text': body_text}
            if 'PIN=' in body_text:
                for part in body_text.split('\t'):
                    if part.startswith('PIN='):
                        user_id = part.split('=')[1]
    except Exception as e:
        raw_data = {'error': str(e)}

    return str(user_id).strip() if user_id else None, raw_data


@csrf_exempt
def universal_webhook(request, token):
    # Qurilmani token orqali tekshiramiz
    try:
        device = Device.objects.get(api_token=token, is_active=True)
    except Device.DoesNotExist:
        return JsonResponse({'status': 'error', 'message': 'Qurilma topilmadi yoki faol emas'}, status=404)

    if request.method in ['POST', 'GET']:
        user_id, raw_data = parse_device_payload(device.brand, request)

        if not user_id:
            return JsonResponse({'status': 'ignored', 'message': 'Xodim ID si aniqlanmadi', 'received': raw_data}, status=200)

        # Bazadan xodimni qidiramiz
        employee = Employee.objects.filter(device_user_id=user_id, is_active=True).first()
        if not employee:
            return JsonResponse({'status': 'error', 'message': f'ID {user_id} li xodim bazada yoq'}, status=404)

        # Kirish yoki chiqish ekanini avtomatik aniqlash (bugungi oxirgi harakatiga qarab)
        today = timezone.now().date()
        last_log = AttendanceLog.objects.filter(employee=employee, timestamp__date=today).first()
        event_type = 'out' if (last_log and last_log.event_type == 'in') else 'in'

        # Davomat jurnaliga yozamiz
        AttendanceLog.objects.create(
            employee=employee,
            device=device,
            timestamp=timezone.now(),
            event_type=event_type,
            raw_data=raw_data
        )

        return JsonResponse({
            'status': 'success',
            'employee': employee.full_name,
            'event': event_type,
            'time': timezone.now().strftime('%H:%M:%S')
        }, status=200)

    return JsonResponse({'status': 'error', 'message': 'Noto‘g‘ri so‘rov turi'}, status=405)
def dashboard_view(request):
    today = timezone.now().date()
    total_employees = Employee.objects.filter(is_active=True).count()
    today_logs = AttendanceLog.objects.filter(timestamp__date=today).select_related('employee', 'device')

    present_employees = set()
    late_employees = set()
    logs_data = []

    for log in today_logs:
        is_late = False
        if log.event_type == 'in':
            present_employees.add(log.employee.id)
            if log.timestamp.time() > log.employee.work_start_time:
                is_late = True
                late_employees.add(log.employee.id)
        logs_data.append({'log': log, 'is_late': is_late})

    present_count = len(present_employees)
    late_count = len(late_employees)
    on_time_count = max(0, present_count - late_count)
    absent_count = max(0, total_employees - present_count)

    context = {
        'today': today,
        'total_employees': total_employees,
        'present_count': present_count,
        'late_count': late_count,
        'on_time_count': on_time_count,
        'absent_count': absent_count,
        'logs_data': logs_data,
    }
    return render(request, 'dashboard.html', context)