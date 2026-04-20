from __future__ import annotations

import io
from pathlib import Path

import pytest

from apps.assets.services import script_loader


@pytest.mark.django_db
def test_load_sync_script(tmp_path, monkeypatch):
    # Arrange: point SCRIPTS_ROOT to a temp directory and write a dummy script.
    scripts_root = tmp_path / "scripts"
    scripts_root.mkdir()
    monkeypatch.setattr(script_loader, "SCRIPTS_ROOT", scripts_root, raising=True)

    script_id = "dummy"
    script_file = scripts_root / f"{script_id}.py"
    script_file.write_text(
        "def run(context):\n"
        "    return [{'asset_type': context.get('asset_type', 'test'), 'source': 'test', 'external_id': '1', 'metadata': {}}]\n",
        encoding="utf-8",
    )

    # Act
    run = script_loader.load_sync_script(script_id)
    result = run({"asset_type": "test-model"})

    # Assert
    assert isinstance(result, list)
    assert result and result[0]["asset_type"] == "test-model"


def test_save_sync_script(tmp_path, monkeypatch):
    # Arrange
    scripts_root = tmp_path / "scripts"
    monkeypatch.setattr(script_loader, "SCRIPTS_ROOT", scripts_root, raising=True)

    script_id = "sample"
    content = b"def run(context):\n    return []\n"
    file_obj = io.BytesIO(content)

    # Act
    path = script_loader.save_sync_script(script_id, file_obj)

    # Assert
    assert path.exists()
    assert path.read_bytes() == content


def test_load_sync_script_syntax_error(tmp_path, monkeypatch):
    scripts_root = tmp_path / "scripts"
    scripts_root.mkdir()
    monkeypatch.setattr(script_loader, "SCRIPTS_ROOT", scripts_root, raising=True)

    script_id = "bad"
    script_file = scripts_root / f"{script_id}.py"
    script_file.write_text("def run(context):\n    return [\n", encoding="utf-8")

    with pytest.raises(script_loader.ScriptLoadError, match="语法错误"):
        script_loader.load_sync_script(script_id)


def test_load_sync_script_rejects_top_level_execution(tmp_path, monkeypatch):
    scripts_root = tmp_path / "scripts"
    scripts_root.mkdir()
    monkeypatch.setattr(script_loader, "SCRIPTS_ROOT", scripts_root, raising=True)

    marker_path = tmp_path / "executed.txt"
    script_id = "unsafe"
    script_file = scripts_root / f"{script_id}.py"
    script_file.write_text(
        "from pathlib import Path\n"
        f"Path({str(marker_path)!r}).write_text('boom', encoding='utf-8')\n"
        "def run(context):\n"
        "    return []\n",
        encoding="utf-8",
    )

    with pytest.raises(script_loader.ScriptLoadError, match="模块顶层执行代码"):
        script_loader.load_sync_script(script_id)

    assert not marker_path.exists()
