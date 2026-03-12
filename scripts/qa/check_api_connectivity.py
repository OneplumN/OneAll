#!/usr/bin/env python3
from __future__ import annotations

import argparse
import os
import re
import sys
from pathlib import Path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="校验前端 API 调用与后端路由联通性")
    parser.add_argument("--backend-src", default="backend/src")
    parser.add_argument("--frontend-services", default="frontend/src/services")
    parser.add_argument("--database-module", default="core.settings.database_sqlite")
    return parser.parse_args()


def setup_django(backend_src: Path, database_module: str) -> None:
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "core.settings.base")
    os.environ.setdefault("DJANGO_DATABASE_MODULE", database_module)
    os.environ.setdefault("USE_TIMESCALE", "0")
    sys.path.insert(0, str(backend_src))
    import django

    django.setup()


def flatten_patterns(patterns, prefix: str = ""):
    from django.urls import URLPattern, URLResolver

    flattened = []
    for item in patterns:
        if isinstance(item, URLPattern):
            flattened.append((prefix + str(item.pattern), item.callback))
        elif isinstance(item, URLResolver):
            flattened.extend(flatten_patterns(item.url_patterns, prefix + str(item.pattern)))
    return flattened


def normalize_backend_path(raw: str) -> str:
    path = "/" + raw
    path = path.replace("\\.", ".")
    path = re.sub(r"\(\?P<format>[^)]*\)\/?\??", "", path)
    path = path.replace("^", "").replace("$", "").replace("\\", "")
    path = re.sub(r"\(\?P<[^>]+>\[\^/\.\]\+\)", "<param>", path)
    path = re.sub(r"\(\?P<[^>]+>[^)]*\)", "<param>", path)
    path = re.sub(r"/+", "/", path)
    return path


def collect_backend_routes():
    from django.urls import get_resolver

    route_methods: dict[str, set[str]] = {}
    for raw, callback in flatten_patterns(get_resolver().url_patterns):
        if not raw.startswith("api/"):
            continue

        methods: set[str] = set()
        actions = getattr(callback, "actions", None)
        if actions:
            methods = {method.upper() for method in actions.keys()}
        else:
            view_class = getattr(callback, "view_class", None)
            if view_class and hasattr(view_class, "http_method_names"):
                methods = {
                    method.upper()
                    for method in view_class.http_method_names
                    if hasattr(view_class, method)
                }

        normalized = normalize_backend_path(raw)
        if normalized in {"/api/", "/api/<drf_format_suffix:format>"}:
            continue
        route_methods.setdefault(normalized, set()).update(methods)

    patterns = []
    for path, methods in route_methods.items():
        regex = "^" + re.sub(r"<[^>]+>", r"[^/]+", re.escape(path).rstrip("/")) + "/?$"
        static_score = len([segment for segment in path.split("/") if segment and not segment.startswith("<")])
        param_score = path.count("<")
        patterns.append((re.compile(regex), path, methods, static_score, -param_score))
    return patterns


def collect_frontend_calls(service_dir: Path):
    call_pattern = re.compile(
        r"apiClient\.(get|post|put|patch|delete)\s*(?:<[^>]*>)?\s*\(\s*([`'\"])(.+?)\2",
        re.S,
    )
    calls = []
    for file in sorted(service_dir.glob("*.ts")):
        content = file.read_text(encoding="utf-8")
        for match in call_pattern.finditer(content):
            calls.append((file.name, match.group(1).upper(), match.group(3).strip()))
    return calls


def validate_connectivity(routes, calls):
    unmatched = []
    method_mismatch = []

    for filename, method, path in calls:
        cleaned = path.split("?")[0]
        normalized = "/api" + cleaned if cleaned.startswith("/") else "/api/" + cleaned
        normalized = re.sub(r"\$\{[^}]+\}", "seg", normalized)

        hits = [route for route in routes if route[0].match(normalized)]
        if not hits:
            unmatched.append((filename, method, path))
            continue

        if any(method in methods for _, _, methods, _, _ in hits):
            continue

        ranked = sorted(hits, key=lambda item: (-item[3], item[4], len(item[1])))
        best = ranked[0]
        method_mismatch.append((filename, method, path, best[1], sorted(best[2])))

    return unmatched, method_mismatch


def main() -> int:
    args = parse_args()
    backend_src = Path(args.backend_src).resolve()
    service_dir = Path(args.frontend_services).resolve()

    setup_django(backend_src, args.database_module)
    routes = collect_backend_routes()
    calls = collect_frontend_calls(service_dir)
    unmatched, method_mismatch = validate_connectivity(routes, calls)

    print(f"frontend_calls={len(calls)}")
    print(f"backend_routes={len(routes)}")
    print(f"unmatched={len(unmatched)}")
    print(f"method_mismatch={len(method_mismatch)}")

    if unmatched:
        print("\n[UNMATCHED]")
        for filename, method, path in unmatched:
            print(f"{filename}\t{method}\t{path}")

    if method_mismatch:
        print("\n[METHOD_MISMATCH]")
        for filename, method, path, matched_path, methods in method_mismatch:
            print(f"{filename}\t{method}\t{path}\t=>\t{matched_path}\t({','.join(methods)})")

    return 1 if unmatched or method_mismatch else 0


if __name__ == "__main__":
    raise SystemExit(main())

