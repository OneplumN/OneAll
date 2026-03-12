from __future__ import annotations

import environ

from core.settings.env_loader import load_env

env = environ.Env(
    MYSQL_HOST=(str, "localhost"),
    MYSQL_PORT=(int, 3306),
    MYSQL_DB=(str, "oneall"),
    MYSQL_USER=(str, "oneall"),
    MYSQL_PASSWORD=(str, "oneall"),
    MYSQL_CONN_MAX_AGE=(int, 60),
)

load_env()

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.mysql",
        "NAME": env("MYSQL_DB"),
        "USER": env("MYSQL_USER"),
        "PASSWORD": env("MYSQL_PASSWORD"),
        "HOST": env("MYSQL_HOST"),
        "PORT": env("MYSQL_PORT"),
        "OPTIONS": {
            "charset": "utf8mb4",
            "init_command": "SET sql_mode='STRICT_TRANS_TABLES'",
        },
        "CONN_MAX_AGE": env("MYSQL_CONN_MAX_AGE"),
    }
}

SECRET_TEMPLATES = {
    "MYSQL": {
        "MYSQL_HOST": "mysql",
        "MYSQL_PORT": "3306",
        "MYSQL_DB": "oneall",
        "MYSQL_USER": "oneall",
        "MYSQL_PASSWORD": "change-me",
    }
}
