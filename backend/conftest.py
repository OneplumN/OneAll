from __future__ import annotations

import os
import sys
from pathlib import Path


def _bootstrap_path_and_env() -> None:
    root_dir = Path(__file__).resolve().parent
    src_dir = root_dir / "src"
    if str(src_dir) not in sys.path:
        sys.path.insert(0, str(src_dir))

    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "core.settings.base")
    os.environ.setdefault("DJANGO_DATABASE_MODULE", "core.settings.database_sqlite")


_bootstrap_path_and_env()
