#!/usr/bin/env bash
# Render build step: install, collect static files, migrate, ensure a login.
set -o errexit

pip install --upgrade pip
pip install -r requirements.txt

python manage.py collectstatic --no-input
python manage.py migrate --no-input

# Creates/updates the organiser account when DJANGO_SUPERUSER_* env vars are set.
python manage.py ensure_admin

# Set SEED_DEMO_DATA=1 in the Render dashboard to load the demo festival once.
if [ "${SEED_DEMO_DATA:-0}" = "1" ]; then
    python manage.py seed_demo
fi
