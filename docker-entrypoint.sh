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


echo "Updating email templates..."
if python update_email_template.py; then
    echo "Email templates updated successfully"
else
    echo "Warning: Failed to update email templates, continuing anyway..."
fi

echo "Starting server..."
exec "$@"
