#!/bin/bash
# Entrypoint script for Docker container

set -e

echo "=== Novel Writing Agent - Starting ==="

# Wait for PostgreSQL to be ready
if [ "$DB_ENGINE" = "django.db.backends.postgresql" ]; then
    echo "Waiting for PostgreSQL..."
    while ! nc -z $DB_HOST $DB_PORT; do
        sleep 0.5
    done
    echo "PostgreSQL is ready!"
fi

# Wait for Redis to be ready
echo "Waiting for Redis..."
REDIS_HOST=$(echo $REDIS_URL | sed -n 's/.*\/\/\([^:]*\).*/\1/p')
REDIS_PORT=$(echo $REDIS_URL | sed -n 's/.*:\([0-9]*\)\/.*/\1/p')
REDIS_HOST=${REDIS_HOST:-localhost}
REDIS_PORT=${REDIS_PORT:-6379}

while ! nc -z $REDIS_HOST $REDIS_PORT; do
    sleep 0.5
done
echo "Redis is ready!"

# Create migration files if needed
echo "Creating migration files..."
python manage.py makemigrations --noinput || echo "No new migrations to create"

# Run database migrations
echo "Running database migrations..."
python manage.py migrate --noinput

# Collect static files (only for web/daphne, not celery)
if [[ "$@" == *"daphne"* ]] || [[ "$@" == *"runserver"* ]]; then
    echo "Collecting static files..."
    python manage.py collectstatic --noinput --clear
else
    echo "Skipping static files collection (not a web server)"
fi

# Create cache table if using database cache
# python manage.py createcachetable

echo "=== Startup Complete ==="

# Execute the main command
exec "$@"
