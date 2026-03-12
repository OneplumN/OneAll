from __future__ import annotations

import os
from importlib import import_module
from pathlib import Path

import environ

from core.settings.env_loader import load_env

BASE_DIR = Path(__file__).resolve().parent.parent.parent

env = environ.Env(
    DEBUG=(bool, False),
    SECRET_KEY=(str, "oneall-secret-key"),
    ALLOWED_HOSTS=(list[str], ["localhost", "127.0.0.1"]),
    LANGUAGE_CODE=(str, "zh-hans"),
    TIME_ZONE=(str, "Asia/Shanghai"),
    JWT_ACCESS_TOKEN_TTL_SECONDS=(int, 86400),
    IP_REGEX_MAX_RESULTS=(int, 2000),
    IP_REGEX_PLUGIN_SLUG=(str, "ip-regex-helper"),
    CONSOLE_BASE_URL=(str, ""),
)

load_env()

CONSOLE_BASE_URL = env("CONSOLE_BASE_URL", default="")
SECRET_KEY = env("SECRET_KEY")
DEBUG = env("DEBUG")
ALLOWED_HOSTS = env.list("ALLOWED_HOSTS", default=["localhost", "127.0.0.1"])

LANGUAGE_CODE = env("LANGUAGE_CODE")
TIME_ZONE = env("TIME_ZONE")
USE_I18N = True
USE_TZ = True

JWT_ACCESS_TOKEN_TTL_SECONDS = env("JWT_ACCESS_TOKEN_TTL_SECONDS", default=86400)

IP_REGEX_MAX_RESULTS = env("IP_REGEX_MAX_RESULTS", default=2000)
IP_REGEX_PLUGIN_SLUG = env("IP_REGEX_PLUGIN_SLUG", default="ip-regex-helper")

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "rest_framework",
    "rest_framework.authtoken",
    "corsheaders",
    "apps.core",
    "apps.probes",
    "apps.dashboard",
    "apps.settings",
    "apps.monitoring",
    "apps.assets",
    "apps.analytics",
    "apps.tools",
    "apps.knowledge",
]

MIDDLEWARE = [
    "corsheaders.middleware.CorsMiddleware",
    "django.middleware.security.SecurityMiddleware",
    "apps.core.middleware.request_timing.RequestTimingMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "core.urls"
WSGI_APPLICATION = "core.wsgi.application"
ASGI_APPLICATION = "core.asgi.application"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    }
]

STATIC_URL = "static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
STATICFILES_DIRS = [BASE_DIR / "static"]

MEDIA_URL = "media/"
MEDIA_ROOT = BASE_DIR / "media"

REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": [
        "core.auth.jwt.JWTAuthentication",
        "rest_framework.authentication.TokenAuthentication",
        "rest_framework.authentication.SessionAuthentication",
    ],
    "DEFAULT_PERMISSION_CLASSES": [
        "rest_framework.permissions.IsAuthenticated",
    ],
    "DEFAULT_SCHEMA_CLASS": "drf_spectacular.openapi.AutoSchema",
}

SPECTACULAR_SETTINGS = {
    "TITLE": "OneAll Platform API",
    "DESCRIPTION": "OneAll 智能运维平台 REST API",
    "VERSION": "0.1.0",
    "SERVE_INCLUDE_SCHEMA": False,
}

CORS_DEFAULT_ORIGINS = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    "http://0.0.0.0:5173",
]
CORS_ALLOWED_ORIGINS = env.list(
    "CORS_ALLOWED_ORIGINS",
    default=list(CORS_DEFAULT_ORIGINS),
)
CORS_ALLOWED_ORIGIN_REGEXES = env.list(
    "CORS_ALLOWED_ORIGIN_REGEXES",
    default=[
        r"^http://172\.\d{1,3}\.\d{1,3}\.\d{1,3}:5173$",
        r"^http://192\.168\.\d{1,3}\.\d{1,3}:5173$",
    ],
)
CSRF_TRUSTED_ORIGINS = env.list(
    "CSRF_TRUSTED_ORIGINS",
    default=list(CORS_ALLOWED_ORIGINS),
)
CORS_ALLOW_CREDENTIALS = True

AUTH_USER_MODEL = "core.User"

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

DEFAULT_DATABASE_MODULE = "core.settings.database"
SECRET_TEMPLATES: dict[str, dict[str, str]] = {}

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": BASE_DIR / "db.sqlite3",
    }
}

module_path = os.getenv("DJANGO_DATABASE_MODULE", DEFAULT_DATABASE_MODULE)
try:
    database_module = import_module(module_path)
except ModuleNotFoundError:
    database_module = None
else:
    DATABASES = getattr(database_module, "DATABASES", DATABASES)
    SECRET_TEMPLATES = getattr(database_module, "SECRET_TEMPLATES", {})

USE_TIMESCALE = env.bool("USE_TIMESCALE", default=True)
if USE_TIMESCALE:
    try:
        from core.settings.timescale import (
            HYPERTABLE_BOOTSTRAP_SQL,
            TIMESCALE_DATABASE,
        )
    except ModuleNotFoundError:
        TIMESCALE_DATABASE = None
        HYPERTABLE_BOOTSTRAP_SQL = ""
    else:
        DATABASES.setdefault("timescale", TIMESCALE_DATABASE)
else:
    TIMESCALE_DATABASE = None
    HYPERTABLE_BOOTSTRAP_SQL = ""

try:
    from core.observability import LOGGING_CONFIG as OBS_LOGGING_CONFIG
except ModuleNotFoundError:
    OBS_LOGGING_CONFIG = {}

LOGGING_CONFIG = "logging.config.dictConfig"
LOGGING = OBS_LOGGING_CONFIG

CELERY_BROKER_URL = env("CELERY_BROKER_URL", default="redis://localhost:6379/0")
CELERY_RESULT_BACKEND = env("CELERY_RESULT_BACKEND", default="redis://localhost:6379/1")
CELERY_ACCEPT_CONTENT = ["json"]
CELERY_TASK_SERIALIZER = "json"
CELERY_RESULT_SERIALIZER = "json"
CELERY_TIMEZONE = TIME_ZONE

try:
    from workers.config import (
        CELERY_BEAT_SCHEDULE,
        CELERY_IMPORTS,
        CELERY_TASK_DEFAULT_QUEUE,
        CELERY_TASK_QUEUES,
        CELERY_TASK_CREATE_MISSING_QUEUES,
        CELERY_TASK_ROUTES,
    )
except ModuleNotFoundError:
    CELERY_TASK_ROUTES = {}
    CELERY_BEAT_SCHEDULE = {}
    CELERY_IMPORTS = ()
    CELERY_TASK_QUEUES = ()
    CELERY_TASK_DEFAULT_QUEUE = "celery"
    CELERY_TASK_CREATE_MISSING_QUEUES = True

ZABBIX_API_URL = env("ZABBIX_API_URL", default="")
ZABBIX_API_TOKEN = env("ZABBIX_API_TOKEN", default="")
ZABBIX_API_TIMEOUT = env.int("ZABBIX_API_TIMEOUT", default=10)
ZABBIX_VERIFY_TLS = env.bool("ZABBIX_VERIFY_TLS", default=True)

DETECTION_MAX_ACTIVE_TASKS = env.int("DETECTION_MAX_ACTIVE_TASKS", default=5)
