#!/bin/bash
set -e

echo "Waiting for database..."
while ! nc -z ${DATABASE_HOST:-db} ${DATABASE_PORT:-5432}; do
  sleep 0.1
done
echo "Database started"

echo "Running migrations..."
python manage.py migrate

echo "Creating superuser if it doesn't exist..."
python manage.py shell -c "
from django.contrib.auth.models import User;
from api.models import UserProfile;
if not User.objects.filter(username='admin').exists():
    user = User.objects.create_superuser('admin', 'admin@example.com', 'admin123');
    UserProfile.objects.create(user=user, role='admin', is_verified=True);
    print('Superuser created');
else:
    print('Superuser already exists');
"

echo "Populating sample data..."
python manage.py populate_sample_data

echo "Starting server..."
exec "$@"
