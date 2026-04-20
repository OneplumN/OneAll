from __future__ import annotations

import ast
import importlib.util
from pathlib import Path
from typing import Any, Callable

from django.core.files.uploadedfile import UploadedFile

SyncScript = Callable[[dict[str, Any]], list[dict[str, Any]]]


# 默认脚本根目录：相对当前 services 包的 scripts 子目录
SCRIPTS_ROOT = Path(__file__).resolve().parent / "scripts"


class ScriptLoadError(RuntimeError):
    """Raised when a sync script cannot be loaded or validated."""


def validate_sync_script_source(script_id: str, source: str) -> None:
    try:
        module = ast.parse(source, filename=f"{script_id}.py")
    except SyntaxError as exc:
        raise ScriptLoadError(f"同步脚本存在语法错误: {exc.msg}") from exc

    run_function: ast.FunctionDef | ast.AsyncFunctionDef | None = None
    for node in module.body:
        if isinstance(node, ast.Expr) and isinstance(getattr(node, "value", None), ast.Constant) and isinstance(
            node.value.value, str
        ):
            continue
        if isinstance(node, (ast.Import, ast.ImportFrom, ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name == "run":
                run_function = node
            continue
        if isinstance(node, ast.Assign):
            if any(not isinstance(target, ast.Name) for target in node.targets):
                raise ScriptLoadError("同步脚本仅允许在模块顶层声明简单变量")
            if not _is_allowed_literal_value(node.value):
                raise ScriptLoadError("同步脚本禁止在模块顶层执行表达式或函数调用")
            continue
        if isinstance(node, ast.AnnAssign):
            if not isinstance(node.target, ast.Name):
                raise ScriptLoadError("同步脚本仅允许在模块顶层声明简单变量")
            if node.value is not None and not _is_allowed_literal_value(node.value):
                raise ScriptLoadError("同步脚本禁止在模块顶层执行表达式或函数调用")
            continue
        raise ScriptLoadError("同步脚本仅允许导入、字面量常量和函数定义，禁止模块顶层执行代码")

    if run_function is None:
        raise ScriptLoadError(f"同步脚本 {script_id} 未定义 run(context) 函数")

    if len(run_function.args.args) < 1:
        raise ScriptLoadError(f"同步脚本 {script_id} 的 run() 必须至少接收一个 context 参数")


def _is_allowed_literal_value(node: ast.AST) -> bool:
    if isinstance(node, ast.Constant):
        return True
    if isinstance(node, (ast.List, ast.Tuple, ast.Set)):
        return all(_is_allowed_literal_value(element) for element in node.elts)
    if isinstance(node, ast.Dict):
        return all(
            (key is None or _is_allowed_literal_value(key)) and _is_allowed_literal_value(value)
            for key, value in zip(node.keys, node.values)
        )
    if isinstance(node, ast.UnaryOp) and isinstance(node.op, (ast.UAdd, ast.USub)):
        return _is_allowed_literal_value(node.operand)
    return False


def load_sync_script(script_id: str) -> SyncScript:
    """Dynamically load a sync script by script_id and return its run(context) callable."""
    script_id = (script_id or "").strip()
    if not script_id:
        raise ScriptLoadError("script_id is required")

    script_path = SCRIPTS_ROOT / f"{script_id}.py"
    if not script_path.exists():
        raise ScriptLoadError(f"Sync script not found: {script_path}")

    try:
        source = script_path.read_text(encoding="utf-8")
    except OSError as exc:
        raise ScriptLoadError(f"读取同步脚本失败: {exc}") from exc

    validate_sync_script_source(script_id, source)

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
