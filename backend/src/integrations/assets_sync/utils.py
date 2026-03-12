from __future__ import annotations

import json
import logging
import os
from pathlib import Path
from typing import Any, Iterable, List, Optional

logger = logging.getLogger(__name__)


def load_records_from_env(
    env_var: str,
    default: Iterable[dict[str, Any]],
    default_filename: Optional[str] = None,
) -> List[dict[str, Any]]:
    """Load records from JSON file specified via env var; fallback to bundled sample."""

    path_value = os.getenv(env_var)
    candidate_paths: List[Path] = []
    seen: set[str] = set()

    if path_value:
        path = Path(path_value)
        candidate_paths.append(path)
        seen.add(str(path))
    if default_filename:
        data_dir = os.getenv("ASSET_SYNC_DATA_DIR")
        if data_dir:
            path = Path(data_dir) / default_filename
            key = str(path)
            if key not in seen:
                candidate_paths.append(path)
                seen.add(key)
        else:
            roots: List[Path] = []
            try:
                repo_root = Path(__file__).resolve().parents[4]
                roots.append(repo_root)
            except IndexError:  # pragma: no cover - defensive fallback
                roots.append(Path.cwd())
            try:
                backend_root = Path(__file__).resolve().parents[3]
                if backend_root not in roots:
                    roots.append(backend_root)
            except IndexError:  # pragma: no cover - defensive fallback
                pass
            for root in roots:
                default_path = root / "data" / default_filename
                key = str(default_path)
                if key not in seen:
                    candidate_paths.append(default_path)
                    seen.add(key)
        bundled = Path(__file__).resolve().parent / 'samples' / default_filename
        if str(bundled) not in seen:
            candidate_paths.append(bundled)

    for path in candidate_paths:
        if not path.exists():
            continue
        try:
            data = json.loads(path.read_text(encoding='utf-8'))
            if isinstance(data, list):
                return data  # type: ignore[return-value]
            logger.warning("Asset sync file %s does not contain a list; skipping", path)
        except json.JSONDecodeError as exc:
            logger.warning("Failed to parse %s: %s", path, exc)

    if path_value:
        logger.warning("Asset sync file %s not usable; falling back to default sample", path_value)
    elif default_filename:
        logger.info("Using bundled sample %s for asset sync", default_filename)
    return list(default)
