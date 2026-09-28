import os
from pathlib import Path

from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent

# Load .env from project root when present (production & local dev with .env file)
load_dotenv(BASE_DIR / ".env")

# ── Security ──────────────────────────────────────────────────────────────────
SECRET_KEY = os.getenv(
    "SECRET_KEY",
    "django-insecure-local-dcrs-development-key-change-in-production",
)

DEBUG = os.getenv("DEBUG", "True") == "True"

_raw_hosts = os.getenv("ALLOWED_HOSTS", "localhost,127.0.0.1,0.0.0.0")
ALLOWED_HOSTS = [h.strip() for h in _raw_hosts.split(",") if h.strip()]

# ── Application ───────────────────────────────────────────────────────────────
INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    # ── Third-party ──────────────────────────────────────────────────────────
    "rest_framework",
    "drf_spectacular",
    # ── Local apps ───────────────────────────────────────────────────────────
    "apps.accounts",
    "apps.localities",
    "apps.citizens",
    "apps.issues",
    "apps.notifications",
    "apps.reports",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
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
                "apps.notifications.context_processors.notifications",
            ],
        },
    },
]

WSGI_APPLICATION = "config.wsgi.application"

# ── Database ──────────────────────────────────────────────────────────────────
# Defaults to SQLite for local dev; set DB_ENGINE in .env for PostgreSQL.
DATABASES = {
    "default": {
        "ENGINE":   os.getenv("DB_ENGINE",   "django.db.backends.sqlite3"),
        "NAME":     os.getenv("DB_NAME",     str(BASE_DIR / "db.sqlite3")),
        "USER":     os.getenv("DB_USER",     ""),
        "PASSWORD": os.getenv("DB_PASSWORD", ""),
        "HOST":     os.getenv("DB_HOST",     ""),
        "PORT":     os.getenv("DB_PORT",     ""),
    }
}

# ── Password validation ───────────────────────────────────────────────────────
AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

# ── Internationalisation ──────────────────────────────────────────────────────
LANGUAGE_CODE = "en-us"
LANGUAGES = [
    ("en", "English"),
    ("sw", "Kiswahili"),
]
TIME_ZONE = "Africa/Dar_es_Salaam"
USE_I18N = True
USE_TZ = True

# ── Static & media ────────────────────────────────────────────────────────────
STATIC_URL = "/static/"
STATICFILES_DIRS = [BASE_DIR / "static"]
STATIC_ROOT = os.getenv("STATIC_ROOT", str(BASE_DIR / "staticfiles"))

MEDIA_URL = "/media/"
MEDIA_ROOT = os.getenv("MEDIA_ROOT", str(BASE_DIR / "media"))

# ── Email ─────────────────────────────────────────────────────────────────────
EMAIL_BACKEND = os.getenv(
    "EMAIL_BACKEND",
    "django.core.mail.backends.console.EmailBackend",
)
DEFAULT_FROM_EMAIL = os.getenv("DEFAULT_FROM_EMAIL", "noreply@dcrs.local")

# ── SMS (SendAfrica) ──────────────────────────────────────────────────────────
# Leave SENDAFRICA_API_KEY blank to fall back to the internal simulator (dev).
SENDAFRICA_BASE_URL = os.getenv("SENDAFRICA_BASE_URL", "https://api.sendafrica.online")
SENDAFRICA_API_KEY = os.getenv("SENDAFRICA_API_KEY", "")
SENDAFRICA_SENDER_ID = os.getenv("SENDAFRICA_SENDER_ID", "")

# ── Auth & session ────────────────────────────────────────────────────────────
AUTH_USER_MODEL = "accounts.User"
# Allow sign-in with either the username or the phone number
AUTHENTICATION_BACKENDS = ["apps.accounts.backends.UsernameOrPhoneBackend"]
LOGIN_URL = "accounts:login"
LOGIN_REDIRECT_URL = "reports:dashboard"
LOGOUT_REDIRECT_URL = "citizens:home"
SESSION_COOKIE_AGE = 1800
SESSION_SAVE_EVERY_REQUEST = True

# ── CSRF & secure cookies ─────────────────────────────────────────────────────
# Django sits behind nginx + HTTPS in production (see DEPLOY.md). nginx forwards
# the original scheme via X-Forwarded-Proto, so tell Django to trust it; otherwise
# admin/forms see "http" and CSRF origin checks fail on the HTTPS site.
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")

# Set in .env in production, e.g.:
#   CSRF_TRUSTED_ORIGINS=https://dcrs.simamia.online,https://www.dcrs.simamia.online
_raw_csrf_origins = os.getenv("CSRF_TRUSTED_ORIGINS", "")
CSRF_TRUSTED_ORIGINS = [o.strip() for o in _raw_csrf_origins.split(",") if o.strip()]

# Enable these in .env once served over HTTPS (never on plain-HTTP local dev):
#   CSRF_COOKIE_SECURE=True SESSION_COOKIE_SECURE=True SECURE_SSL_REDIRECT=True
CSRF_COOKIE_SECURE = os.getenv("CSRF_COOKIE_SECURE", "False") == "True"
CSRF_COOKIE_HTTPONLY = os.getenv("CSRF_COOKIE_HTTPONLY", "False") == "True"
CSRF_COOKIE_SAMESITE = os.getenv("CSRF_COOKIE_SAMESITE", "Lax")
SESSION_COOKIE_SECURE = os.getenv("SESSION_COOKIE_SECURE", "False") == "True"
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SAMESITE = os.getenv("SESSION_COOKIE_SAMESITE", "Lax")
SECURE_SSL_REDIRECT = os.getenv("SECURE_SSL_REDIRECT", "False") == "True"

# ── API layer (DRF) ───────────────────────────────────────────────────────────
# The React + TypeScript SPA consumes /api/v1/**. Auth is the existing Django
# session (UsernameOrPhoneBackend), so SessionAuthentication is all we need —
# it also enforces CSRF on unsafe methods, which the SPA satisfies with the
# X-CSRFToken header (bootstrapped from GET /api/v1/auth/csrf/).
REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": [
        "rest_framework.authentication.SessionAuthentication",
    ],
    "DEFAULT_PERMISSION_CLASSES": [
        "rest_framework.permissions.IsAuthenticated",
    ],
    "DEFAULT_PAGINATION_CLASS": "rest_framework.pagination.PageNumberPagination",
    "PAGE_SIZE": 10,  # mirrors the templates' paginate_by = 10
    "DEFAULT_SCHEMA_CLASS": "drf_spectacular.openapi.AutoSchema",
}

SPECTACULAR_SETTINGS = {
    "TITLE": "DCRS API",
    "DESCRIPTION": "JSON API for the DCRS React + TypeScript frontend.",
    "VERSION": "1.0.0",
    "SERVE_INCLUDE_SCHEMA": False,
}

# ── Misc ─────────────────────────────────────────────────────────────────────
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"
