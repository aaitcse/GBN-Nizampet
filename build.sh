#!/usr/bin/env bash
# Render build step: install dependencies and collect static files.
# Nothing here touches the database - the build environment cannot reach it.
# Migrations and the organiser account are handled by start.sh.
set -o errexit

pip install --upgrade pip
pip install -r requirements.txt

python manage.py collectstatic --no-input
