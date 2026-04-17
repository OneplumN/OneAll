from __future__ import annotations

from pathlib import Path

import environ

from core.settings.env_loader import BASE_DIR

env = environ.Env(
    SQLITE_DB_PATH=(str, str(Path(BASE_DIR) / "test.sqlite3")),
)

DB_FILE = Path(env("SQLITE_DB_PATH"))

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": DB_FILE,
    }
}

SECRET_TEMPLATES = {}
