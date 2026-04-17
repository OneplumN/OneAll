from __future__ import annotations

import importlib.util
from pathlib import Path
from typing import Any, Callable

from django.core.files.uploadedfile import UploadedFile

SyncScript = Callable[[dict[str, Any]], list[dict[str, Any]]]


# 默认脚本根目录：相对当前 services 包的 scripts 子目录
SCRIPTS_ROOT = Path(__file__).resolve().parent / "scripts"


class ScriptLoadError(RuntimeError):
    """Raised when a sync script cannot be loaded or validated."""


def load_sync_script(script_id: str) -> SyncScript:
    """Dynamically load a sync script by script_id and return its run(context) callable."""
    script_id = (script_id or "").strip()
    if not script_id:
        raise ScriptLoadError("script_id is required")

    script_path = SCRIPTS_ROOT / f"{script_id}.py"
    if not script_path.exists():
        raise ScriptLoadError(f"Sync script not found: {script_path}")

    spec = importlib.util.spec_from_file_location(f"assets_sync_{script_id}", script_path)
    if spec is None or spec.loader is None:
        raise ScriptLoadError(f"Failed to load spec for script: {script_path}")

    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)  # type: ignore[call-arg]

    run = getattr(module, "run", None)
    if not callable(run):
        raise ScriptLoadError(f"Sync script {script_id} does not define callable run(context)")

    return run  # type: ignore[return-value]


def save_sync_script(script_id: str, file_obj: UploadedFile | Any) -> Path:
    """Persist uploaded script contents to SCRIPTS_ROOT and return the final path.

    - script_id: logical identifier for the script (usually ties to AssetModel.key)
    - file_obj: Django UploadedFile or any file-like object supporting .read() / .chunks()
    """
    script_id = (script_id or "").strip()
    if not script_id:
        raise ValueError("script_id is required")

    SCRIPTS_ROOT.mkdir(parents=True, exist_ok=True)
    target_path = SCRIPTS_ROOT / f"{script_id}.py"

    # 支持 UploadedFile.chunks() 和普通文件对象.read()
    if hasattr(file_obj, "chunks"):
        iterator = file_obj.chunks()
    else:
        data = file_obj.read()
        iterator = [data]

    with target_path.open("wb") as fp:
        for chunk in iterator:
            if not chunk:
                continue
            fp.write(chunk)

    return target_path

