from __future__ import annotations

import inspect
import json
import sys
import traceback
from pathlib import Path


def _invoke_entrypoint(entrypoint: object, context: dict[str, object]) -> object:
    signature = inspect.signature(entrypoint)
    accepts_args = any(
        parameter.kind in (inspect.Parameter.POSITIONAL_ONLY, inspect.Parameter.POSITIONAL_OR_KEYWORD)
        for parameter in signature.parameters.values()
    )
    accepts_varargs = any(
        parameter.kind == inspect.Parameter.VAR_POSITIONAL
        for parameter in signature.parameters.values()
    )
    if accepts_args or accepts_varargs:
        return entrypoint(context)
    return entrypoint()


def main(argv: list[str]) -> int:
    if len(argv) != 4:
        print("usage: script_channel_runner.py <script_file> <context_file> <result_file>", file=sys.stderr)
        return 2

    script_file = Path(argv[1])
    context_file = Path(argv[2])
    result_file = Path(argv[3])

    try:
        script_content = script_file.read_text(encoding="utf-8")
        context = json.loads(context_file.read_text(encoding="utf-8"))

        namespace: dict[str, object] = {
            "__name__": "__main__",
            "ALERT_CONTEXT": context,
        }
        exec(script_content, namespace)
        entrypoint = namespace.get("main") or namespace.get("run")
        if callable(entrypoint):
            result = _invoke_entrypoint(entrypoint, context)
        else:
            result = namespace.get("RESULT")

        result_file.write_text(
            json.dumps({"ok": True, "result": result}, ensure_ascii=False, default=str),
            encoding="utf-8",
        )
        return 0
    except Exception as exc:
        result_file.write_text(
            json.dumps(
                {
                    "ok": False,
                    "error": str(exc),
                    "traceback": traceback.format_exc(),
                },
                ensure_ascii=False,
            ),
            encoding="utf-8",
        )
        return 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
