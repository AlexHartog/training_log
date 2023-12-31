#!/bin/bash

# Collect static files
echo "Collect static files"
python manage.py collectstatic --noinput --clear

# Apply database migrations
echo "Apply database migrations"
python manage.py migrate

# Start server
echo "Starting server"
gunicorn training_log.wsgi:application --threads=2 --bind 0.0.0.0:8000

