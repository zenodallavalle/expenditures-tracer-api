#!/bin/sh

set -e

python manage.py migrate --no-input

if [ "$EXPENDITURES_TRACER_API_RUN_MODE" = "development" ]; then
    echo "Running in development mode, collecting static files..."
    python manage.py collectstatic --no-input
    echo "Starting server..."
    python manage.py runserver 0.0.0.0:8000 --nothreading
else
    echo "Running in production mode..."
    python -m gunicorn --bind 0.0.0.0:8000 --workers 2 --threads 2 expendituresTracer.wsgi
fi


