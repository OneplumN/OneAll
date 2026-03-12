from __future__ import annotations

import os
from pathlib import Path
from typing import Iterable

import environ

BASE_DIR = Path(__file__).resolve().parent.parent.parent

_LOADED = False


def _candidate_paths() -> Iterable[Path]:
    env_file = os.getenv("DJANGO_ENV_FILE")
    if env_file:
        path = Path(env_file).expanduser()
        if path.exists():
            yield path

    yield BASE_DIR / ".env"
    yield BASE_DIR.parent / ".env"
    yield BASE_DIR.parent / ".env.local"
    yield BASE_DIR.parent.parent / ".env"


def load_env() -> None:
    global _LOADED
    if _LOADED:
        return

    for candidate in _candidate_paths():
        if candidate.exists():
            environ.Env.read_env(candidate)
            _LOADED = True
            return

    _LOADED = True
