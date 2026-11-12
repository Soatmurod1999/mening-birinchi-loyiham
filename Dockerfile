FROM python:3.13-slim

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

COPY requirements.txt /app/
RUN pip install --no-cache-dir -r requirements.txt

COPY . /app/

RUN python manage.py collectstatic --noinput

CMD ["sh", "-c", "python manage.py migrate attendance zero --fake || true && python manage.py migrate && python manage.py createsuperuser --noinput || true && gunicorn core.wsgi:application --bind 0.0.0.0:${PORT:-10000}"]


