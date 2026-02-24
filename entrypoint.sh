#!/bin/bash

# Exit on any error
set -e

echo "Starting Django Hotel Room Booking Backend..."

# Wait for database to be ready
echo "Waiting for database..."
python manage.py wait_for_db

# Create migration files
echo "Creating migration files..."
python manage.py makemigrations --noinput

# Run migrations
echo "Running database migrations..."
python manage.py migrate --noinput

# Collect static files (placeholder for now)
echo "Collecting static files..."
python manage.py collectstatic --noinput --clear

# Create superuser if it doesn't exist (for development)
echo "Checking for superuser..."
python manage.py shell -c "
from django.contrib.auth import get_user_model
User = get_user_model()
if not User.objects.filter(is_superuser=True).exists():
    User.objects.create_superuser('admin', 'admin@example.com', 'admin123')
    print('Superuser created: admin/admin123')
else:
    print('Superuser already exists')
"

# Start the appropriate service based on environment
if [ "$1" = "celery" ]; then
    echo "Starting Celery worker..."
    exec celery -A config worker -l info
elif [ "$1" = "celery-beat" ]; then
    echo "Starting Celery beat..."
    exec celery -A config beat -l info
else
    echo "Starting Gunicorn server (WSGI)..."
    exec gunicorn config.wsgi:application --bind 0.0.0.0:8000 --workers 4 --log-level info
fi
