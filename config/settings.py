"""Django settings for the GBN festival project."""

import os
from pathlib import Path

import dj_database_url

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = os.environ.get(
    "DJANGO_SECRET_KEY", "django-insecure-gbn-dev-key-change-me-in-production"
)
DEBUG = os.environ.get("DJANGO_DEBUG", "1") == "1"
ALLOWED_HOSTS = [
    h.strip() for h in os.environ.get("DJANGO_ALLOWED_HOSTS", "localhost,127.0.0.1,[::1]").split(",") if h.strip()
]
CSRF_TRUSTED_ORIGINS = [
    o.strip() for o in os.environ.get("DJANGO_CSRF_TRUSTED_ORIGINS", "").split(",") if o.strip()
]

# Render publishes the service hostname; trust it without hardcoding the URL.
RENDER_HOSTNAME = os.environ.get("RENDER_EXTERNAL_HOSTNAME")
if RENDER_HOSTNAME:
    ALLOWED_HOSTS.append(RENDER_HOSTNAME)
    CSRF_TRUSTED_ORIGINS.append(f"https://{RENDER_HOSTNAME}")

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "django.contrib.humanize",
    "festival",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    # WhiteNoise serves the collected static files straight from the web
    # process, so Render needs no separate CDN or static file service.
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "config.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
                "festival.context_processors.branding",
            ],
        },
    },
]

WSGI_APPLICATION = "config.wsgi.application"
ASGI_APPLICATION = "config.asgi.application"

# SQLite locally; on Render, DATABASE_URL points at the managed Postgres.
DATABASES = {
    "default": dj_database_url.config(
        default=f"sqlite:///{BASE_DIR / 'db.sqlite3'}",
        conn_max_age=600,
        conn_health_checks=True,
    )
}

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

LANGUAGE_CODE = "en-us"
TIME_ZONE = os.environ.get("DJANGO_TIME_ZONE", "Asia/Kolkata")
USE_I18N = True
USE_TZ = True

STATIC_URL = "static/"
STATICFILES_DIRS = [BASE_DIR / "static"]
STATIC_ROOT = BASE_DIR / "staticfiles"

MEDIA_URL = "media/"
# Point this at a mounted Render disk to keep uploaded photos across deploys.
MEDIA_ROOT = Path(os.environ.get("DJANGO_MEDIA_ROOT", BASE_DIR / "media"))

if not DEBUG:
    # Hashed filenames + gzip/brotli, so browsers can cache static assets hard.
    STORAGES = {
        "default": {"BACKEND": "django.core.files.storage.FileSystemStorage"},
        "staticfiles": {"BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage"},
    }

    # Render terminates TLS at its proxy and forwards this header.
    SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
    SECURE_SSL_REDIRECT = os.environ.get("DJANGO_SECURE_SSL_REDIRECT", "1") == "1"
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    SECURE_HSTS_SECONDS = int(os.environ.get("DJANGO_HSTS_SECONDS", 60 * 60 * 24 * 30))
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SECURE_HSTS_PRELOAD = True
    SECURE_CONTENT_TYPE_NOSNIFF = True
    X_FRAME_OPTIONS = "DENY"

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

LOGIN_URL = "festival:console_login"
LOGIN_REDIRECT_URL = "festival:console_overview"
LOGOUT_REDIRECT_URL = "festival:public_app"

MESSAGE_STORAGE = "django.contrib.messages.storage.session.SessionStorage"

# Django's default logging drops request tracebacks when DEBUG is off, which
# leaves a production 500 looking like a blank wall. Send them to stdout so
# they land in the platform log (Render, Docker, journald, anything).
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "simple": {"format": "[{levelname}] {asctime} {name}: {message}", "style": "{"},
    },
    "handlers": {
        "console": {"class": "logging.StreamHandler", "formatter": "simple"},
    },
    "root": {"handlers": ["console"], "level": "INFO"},
    "loggers": {
        "django.request": {"handlers": ["console"], "level": "ERROR", "propagate": False},
        "django.db.backends": {"handlers": ["console"], "level": "WARNING", "propagate": False},
    },
}

# Uploaded festival photos are capped so a phone photo does not blow up the disk.
DATA_UPLOAD_MAX_MEMORY_SIZE = 10 * 1024 * 1024
FILE_UPLOAD_MAX_MEMORY_SIZE = 10 * 1024 * 1024

# Caps on what an attendee can upload to the gallery.
FEST_MAX_IMAGE_MB = int(os.environ.get("FEST_MAX_IMAGE_MB", 10))
FEST_MAX_VIDEO_MB = int(os.environ.get("FEST_MAX_VIDEO_MB", 25))

# Attendee submissions go live only after an organiser approves them.
FEST_AUTO_APPROVE_PHOTOS = os.environ.get("FEST_AUTO_APPROVE_PHOTOS", "0") == "1"

# --------------------------------------------------------------------------- #
# Branding - the festival name shown across the app, the console and the admin.
# Change FEST_BRAND here (or in the environment) and every page follows.
# --------------------------------------------------------------------------- #
FEST_BRAND = os.environ.get("FEST_BRAND", "GBN")
FEST_BRAND_FULL = os.environ.get("FEST_BRAND_FULL", f"{FEST_BRAND} Connect")
FEST_TAGLINE = os.environ.get("FEST_TAGLINE", "Festival Companion")

# Shown on the home screen. Dates are display-only; the schedule itself is
# organised by Day 1 / Day 2 / Day 3 in the console.
FEST_EVENT_NAME = os.environ.get("FEST_EVENT_NAME", "Ganesh Utsav")
# Banner behind the home screen hero, as a path inside static/. Bundled with
# the code so it survives deploys; set to "" to fall back to the newest
# approved gallery photo instead.
FEST_HERO_IMAGE = os.environ.get("FEST_HERO_IMAGE", "img/hero.jpg")
FEST_VENUE = os.environ.get("FEST_VENUE", "GBN Community, Nizampet")
FEST_DATES = os.environ.get("FEST_DATES", "14 - 20 September 2026")
# The schedule builds its Day 1..Day N tabs from this range.
FEST_START_DATE = os.environ.get("FEST_START_DATE", "2026-09-14")
FEST_END_DATE = os.environ.get("FEST_END_DATE", "2026-09-20")
FEST_WELCOME = os.environ.get(
    "FEST_WELCOME",
    "Seven days of aarti, music, food and light across the campus. "
    "Save what you love, vote for the sets, and send us your best shots.",
)
