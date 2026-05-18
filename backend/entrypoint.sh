#!/bin/sh
set -e

# Only run migrations and collectstatic from the backend container
# Celery container sets RUN_MIGRATIONS=false to skip this
if [ "${RUN_MIGRATIONS:-true}" = "true" ]; then
    echo ">>> Running database migrations..."
    python manage.py migrate --noinput

    echo ">>> Collecting static files..."
    python manage.py collectstatic --noinput --clear

    echo ">>> Seeding initial data (super admin + sample orgs)..."
    python seed_data.py
fi

echo ">>> Starting: $@"
exec "$@"
