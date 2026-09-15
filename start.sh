#!/usr/bin/env bash
# Render start command: bring the database up to date, then serve.
# This runs inside the service network, where the Postgres host resolves.
set -o errexit

# Gives the database a moment to wake, and explains itself if it never does.
python manage.py wait_for_db --retries 10 --delay 3

python manage.py migrate --no-input

# Creates/updates the organiser account when DJANGO_SUPERUSER_* env vars are set.
python manage.py ensure_admin

# Set LOAD_PROGRAMME=1 in the Render dashboard to load the real cultural
# programme (idempotent - safe to leave on).
if [ "${LOAD_PROGRAMME:-0}" = "1" ]; then
    python manage.py load_programme
fi

# Set SEED_DEMO_DATA=1 to load demo photos, polls and feedback instead.
if [ "${SEED_DEMO_DATA:-0}" = "1" ]; then
    python manage.py seed_demo
fi

exec gunicorn config.wsgi:application
