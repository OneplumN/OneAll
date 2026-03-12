from __future__ import annotations

from pathlib import Path

from core.settings.env_loader import BASE_DIR

DB_FILE = Path(BASE_DIR) / "test.sqlite3"

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": DB_FILE,
    }
}

SECRET_TEMPLATES = {}
