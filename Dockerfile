FROM python:3.13-slim

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

COPY requirements.txt /app/
RUN pip install --no-cache-dir -r requirements.txt

COPY . /app/

RUN python manage.py collectstatic --noinput

CMD ["sh", "-c", "python manage.py shell -c 'from django.db import connection; c = connection.cursor(); c.execute(\"DROP TABLE IF EXISTS attendance_attendancelog, attendance_employee, attendance_device, attendance_company CASCADE; DELETE FROM django_migrations WHERE app = %s;\", [\"attendance\"])' && python manage.py migrate && python manage.py createsuperuser --noinput || true && gunicorn core.wsgi:application --bind 0.0.0.0:${PORT:-10000}"]



