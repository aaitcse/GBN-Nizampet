#!/usr/bin/env bash
# Render start command: bring the database up to date, then serve.
# This runs inside the service network, where the Postgres host resolves.
set -o errexit

python manage.py migrate --no-input

# Creates/updates the organiser account when DJANGO_SUPERUSER_* env vars are set.
python manage.py ensure_admin

# Set SEED_DEMO_DATA=1 in the Render dashboard to load the demo festival.
if [ "${SEED_DEMO_DATA:-0}" = "1" ]; then
    python manage.py seed_demo
fi

exec gunicorn config.wsgi:application
