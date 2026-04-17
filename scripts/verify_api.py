#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable

import requests


@dataclass(frozen=True)
class CheckResult:
    name: str
    method: str
    url: str
    ok: bool
    status_code: int | None
    detail: str


def _normalize_api_base(value: str) -> str:
    base = (value or "").strip().rstrip("/")
    if not base:
        return "http://127.0.0.1:8000/api"
    if base.endswith("/api"):
        return base
    if base.endswith("/api/"):
        return base.rstrip("/")
    return base + "/api"


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[1]


def _run(cmd: list[str], *, cwd: Path | None = None) -> str:
    completed = subprocess.run(cmd, capture_output=True, text=True, check=True, cwd=str(cwd) if cwd else None)
    return completed.stdout.strip()


def generate_token_via_django(*, username: str) -> str:
    repo_root = _repo_root()
    code = (
        "from django.contrib.auth import get_user_model\n"
        "from core.auth.jwt import generate_access_token\n"
        "User=get_user_model()\n"
        f"u=User.objects.get(username={username!r})\n"
        "print(generate_access_token(u))\n"
    )
    manage_path = repo_root / "backend" / "src" / "manage.py"
    return _run(["python3", str(manage_path), "shell", "-c", code], cwd=repo_root)


def login_and_get_token(*, api_base: str, username: str, password: str) -> str:
    resp = requests.post(
        f"{api_base}/auth/login",
        json={"username": username, "password": password},
        timeout=15,
    )
    resp.raise_for_status()
    payload = resp.json()
    token = payload.get("access_token")
    if not token:
        raise RuntimeError("登录响应缺少 access_token")
    return str(token)


def request_json(
    *,
    name: str,
    method: str,
    url: str,
    headers: dict[str, str] | None = None,
    params: dict[str, Any] | None = None,
    json_body: Any | None = None,
    expected: Iterable[int] = (200,),
    timeout: int = 20,
) -> CheckResult:
    try:
        resp = requests.request(
            method=method,
            url=url,
            headers=headers,
            params=params,
            json=json_body,
            timeout=timeout,
            allow_redirects=True,
        )
    except requests.RequestException as exc:
        return CheckResult(
            name=name,
            method=method,
            url=url,
            ok=False,
            status_code=None,
            detail=f"请求失败：{exc}",
        )

    status_code = resp.status_code
    ok = status_code in set(int(x) for x in expected)

    detail = f"HTTP {status_code}"
    try:
        data = resp.json()
        if isinstance(data, dict) and "detail" in data:
            detail += f" | detail={data.get('detail')!r}"
    except ValueError:
        text = (resp.text or "").strip()
        if text:
            detail += f" | body={text[:200]!r}"

    return CheckResult(
        name=name,
        method=method,
        url=url,
        ok=ok,
        status_code=status_code,
        detail=detail,
    )


def _print_result(result: CheckResult) -> None:
    status = "通过" if result.ok else "失败"
    print(f"[{status}] {result.name} | {result.method} {result.url} | {result.detail}")


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description="按顺序验证 one-pro 后端 API（HTTP 真实调用）")
    parser.add_argument("--api-base", default=os.getenv("API_BASE", ""), help="API 基础地址（默认 http://127.0.0.1:8000/api）")
    parser.add_argument("--token", default=os.getenv("TOKEN", ""), help="Bearer Token（可选）")
    parser.add_argument("--username", default=os.getenv("USERNAME", ""), help="登录用户名（可选）")
    parser.add_argument("--password", default=os.getenv("PASSWORD", ""), help="登录密码（可选）")
    parser.add_argument("--django-user", default=os.getenv("DJANGO_USER", "admin"), help="用 Django 生成 token 的用户名（默认 admin）")
    parser.add_argument("--write", action="store_true", help="执行会写入数据库的验证（创建拨测任务/创建工单申请/切换插件等）")
    args = parser.parse_args(argv)

    api_base = _normalize_api_base(args.api_base)

    token = (args.token or "").strip()
    if not token and args.username and args.password:
        try:
            token = login_and_get_token(api_base=api_base, username=args.username, password=args.password)
            print("已通过登录接口获取 token。")
        except Exception as exc:
            print(f"登录获取 token 失败，将尝试用 Django 生成 token：{exc}")

    if not token:
        token = generate_token_via_django(username=args.django_user)
        print(f"已通过 Django 生成 token（用户：{args.django_user}）。")

    auth_headers = {"Authorization": f"Bearer {token}"}

    results: list[CheckResult] = []

    # 1) Public / Auth
    results.append(
        request_json(
            name="公共品牌信息",
            method="GET",
            url=f"{api_base}/public/branding",
            expected=(200,),
        )
    )
    results.append(
        request_json(
            name="当前用户信息",
            method="GET",
            url=f"{api_base}/auth/me",
            headers=auth_headers,
            expected=(200,),
        )
    )
    results.append(
        request_json(
            name="审计日志列表",
            method="GET",
            url=f"{api_base}/audit/logs",
            headers=auth_headers,
            expected=(200,),
        )
    )

    # 2) Settings
    results.append(
        request_json(
            name="系统设置读取",
            method="GET",
            url=f"{api_base}/settings/system",
            headers=auth_headers,
            expected=(200, 403),
        )
    )
    results.append(
        request_json(
            name="插件配置列表",
            method="GET",
            url=f"{api_base}/settings/plugins/",
            headers=auth_headers,
            expected=(200,),
        )
    )

    # 3) Probes
    probes_list = requests.get(f"{api_base}/probes/nodes/", headers=auth_headers, timeout=20).json()
    results.append(
        CheckResult(
            name="探针节点列表",
            method="GET",
            url=f"{api_base}/probes/nodes/",
            ok=True,
            status_code=200,
            detail=f"HTTP 200 | items={len(probes_list) if isinstance(probes_list, list) else 'unknown'}",
        )
    )

    # 4) Dashboard（后端带尾斜杠）
    results.append(
        request_json(
            name="驾驶舱概览",
            method="GET",
            url=f"{api_base}/dashboard/overview/",
            headers=auth_headers,
            expected=(200,),
        )
    )
    results.append(
        request_json(
            name="驾驶舱告警摘要",
            method="GET",
            url=f"{api_base}/dashboard/alerts-summary/",
            headers=auth_headers,
            params={"limit": 5},
            expected=(200,),
        )
    )
    results.append(
        request_json(
            name="驾驶舱待办",
            method="GET",
            url=f"{api_base}/dashboard/todos/",
            headers=auth_headers,
            params={"limit": 5},
            expected=(200,),
        )
    )
    results.append(
        request_json(
            name="驾驶舱蜂窝图",
            method="GET",
            url=f"{api_base}/dashboard/detection-grid/",
            headers=auth_headers,
            params={"limit": 50},
            expected=(200,),
        )
    )
    results.append(
        request_json(
            name="驾驶舱证书告警",
            method="GET",
            url=f"{api_base}/dashboard/certificate-alerts/",
            headers=auth_headers,
            params={"limit": 12},
            expected=(200,),
        )
    )

    # 5) Monitoring / Detection
    if args.write:
        oneoff = requests.post(
            f"{api_base}/detection/one-off",
            headers=auth_headers,
            json={"target": "https://example.com", "protocol": "HTTPS", "timeout_seconds": 10},
            timeout=20,
        )
        allowed = {202, 400, 429}
        results.append(
            CheckResult(
                name="一次性拨测提交",
                method="POST",
                url=f"{api_base}/detection/one-off",
                ok=oneoff.status_code in allowed,
                status_code=oneoff.status_code,
                detail=f"HTTP {oneoff.status_code}",
            )
        )
        if oneoff.status_code == 202:
            try:
                detection_id = oneoff.json().get("id")
            except Exception:
                detection_id = None
            if detection_id:
                results.append(
                    request_json(
                        name="一次性拨测详情",
                        method="GET",
                        url=f"{api_base}/detection/tasks/{detection_id}",
                        headers=auth_headers,
                        expected=(200,),
                    )
                )

        # 创建工单申请 -> 管理员审批通过（平台内审批）
        request_payload = {
            "title": "API 自动化验证申请",
            "target": "https://example.com",
            "system_name": "自动化验证",
            "network_type": "internet",
            "protocol": "HTTPS",
            "frequency_minutes": 5,
            "expected_status_codes": [200],
        }
        created_req = requests.post(
            f"{api_base}/monitoring/requests",
            headers=auth_headers,
            json=request_payload,
            timeout=30,
        )
        results.append(
            CheckResult(
                name="工单申请创建（待审批）",
                method="POST",
                url=f"{api_base}/monitoring/requests",
                ok=created_req.status_code == 201,
                status_code=created_req.status_code,
                detail=f"HTTP {created_req.status_code}",
            )
        )
        created_id = None
        if created_req.status_code == 201:
            try:
                created_id = (created_req.json() or {}).get("id")
            except Exception:
                created_id = None

        if created_id:
            approved = requests.post(
                f"{api_base}/monitoring/requests/{created_id}/approve",
                headers=auth_headers,
                json={},
                timeout=30,
            )
            results.append(
                CheckResult(
                    name="工单申请审批通过（管理员）",
                    method="POST",
                    url=f"{api_base}/monitoring/requests/{created_id}/approve",
                    ok=approved.status_code == 200,
                    status_code=approved.status_code,
                    detail=f"HTTP {approved.status_code}",
                )
            )

        # 驳回 -> 修改 -> 重新提交 -> 审批通过（用于验证“仅驳回可修改/需重新提交”规则）
        created_req2 = requests.post(
            f"{api_base}/monitoring/requests",
            headers=auth_headers,
            json={
                "title": "API 自动化验证申请-驳回链路",
                "target": "https://example.com",
                "system_name": "自动化验证",
                "network_type": "internet",
                "protocol": "HTTPS",
                "frequency_minutes": 5,
                "expected_status_codes": [200],
            },
            timeout=30,
        )
        results.append(
            CheckResult(
                name="工单申请创建（用于驳回链路）",
                method="POST",
                url=f"{api_base}/monitoring/requests",
                ok=created_req2.status_code == 201,
                status_code=created_req2.status_code,
                detail=f"HTTP {created_req2.status_code}",
            )
        )
        rejected_id = None
        if created_req2.status_code == 201:
            try:
                rejected_id = (created_req2.json() or {}).get("id")
            except Exception:
                rejected_id = None

        if rejected_id:
            rejected = requests.post(
                f"{api_base}/monitoring/requests/{rejected_id}/reject",
                headers=auth_headers,
                json={"reason": "自动化验证：驳回后允许修改并重新提交"},
                timeout=30,
            )
            results.append(
                CheckResult(
                    name="工单申请驳回（管理员）",
                    method="POST",
                    url=f"{api_base}/monitoring/requests/{rejected_id}/reject",
                    ok=rejected.status_code == 200,
                    status_code=rejected.status_code,
                    detail=f"HTTP {rejected.status_code}",
                )
            )

            patched = requests.patch(
                f"{api_base}/monitoring/requests/{rejected_id}",
                headers=auth_headers,
                json={"title": "API 自动化验证申请-驳回后已修改", "frequency_minutes": 15},
                timeout=30,
            )
            results.append(
                CheckResult(
                    name="工单申请修改（仅驳回后允许）",
                    method="PATCH",
                    url=f"{api_base}/monitoring/requests/{rejected_id}",
                    ok=patched.status_code == 200,
                    status_code=patched.status_code,
                    detail=f"HTTP {patched.status_code}",
                )
            )

            resubmitted = requests.post(
                f"{api_base}/monitoring/requests/{rejected_id}/resubmit",
                headers=auth_headers,
                json={},
                timeout=30,
            )
            results.append(
                CheckResult(
                    name="工单申请重新提交",
                    method="POST",
                    url=f"{api_base}/monitoring/requests/{rejected_id}/resubmit",
                    ok=resubmitted.status_code == 200,
                    status_code=resubmitted.status_code,
                    detail=f"HTTP {resubmitted.status_code}",
                )
            )

            approved2 = requests.post(
                f"{api_base}/monitoring/requests/{rejected_id}/approve",
                headers=auth_headers,
                json={},
                timeout=30,
            )
            results.append(
                CheckResult(
                    name="工单申请二次审批通过（驳回链路）",
                    method="POST",
                    url=f"{api_base}/monitoring/requests/{rejected_id}/approve",
                    ok=approved2.status_code == 200,
                    status_code=approved2.status_code,
                    detail=f"HTTP {approved2.status_code}",
                )
            )

    results.append(
        request_json(
            name="监控申请列表",
            method="GET",
            url=f"{api_base}/monitoring/requests",
            headers=auth_headers,
            expected=(200,),
        )
    )
    results.append(
        request_json(
            name="拨测历史查询",
            method="GET",
            url=f"{api_base}/monitoring/tasks/history",
            headers=auth_headers,
            expected=(200,),
        )
    )
    results.append(
        request_json(
            name="CMDB 域名校验（本地资产匹配）",
            method="GET",
            url=f"{api_base}/detection/cmdb/validate",
            headers=auth_headers,
            params={"domain": "example.com"},
            expected=(200, 400),
        )
    )

    # 6) Assets
    assets_query = requests.get(
        f"{api_base}/assets/records/query",
        headers=auth_headers,
        params={"limit": 5, "offset": 0, "include_facets": True},
        timeout=30,
    )
    results.append(
        CheckResult(
            name="资产查询（含 facets）",
            method="GET",
            url=f"{api_base}/assets/records/query",
            ok=assets_query.status_code == 200,
            status_code=assets_query.status_code,
            detail=f"HTTP {assets_query.status_code}",
        )
    )

    # 资产同步：为了尽量不污染数据，默认只跑 IPMP（当前默认空数据源）
    sync_resp = requests.post(
        f"{api_base}/assets/sync",
        headers=auth_headers,
        json={"mode": "sync", "sources": ["IPMP"]},
        timeout=60,
    )
    results.append(
        CheckResult(
            name="资产同步（最小化：仅 IPMP）",
            method="POST",
            url=f"{api_base}/assets/sync",
            ok=sync_resp.status_code == 200,
            status_code=sync_resp.status_code,
            detail=f"HTTP {sync_resp.status_code}",
        )
    )
    run_id = None
    if sync_resp.status_code == 200:
        try:
            run_id = (sync_resp.json() or {}).get("run_id")
        except Exception:
            run_id = None

    results.append(
        request_json(
            name="资产同步历史列表",
            method="GET",
            url=f"{api_base}/assets/sync/runs",
            headers=auth_headers,
            expected=(200,),
        )
    )
    if run_id:
        results.append(
            request_json(
                name="资产同步详情（含变更）",
                method="GET",
                url=f"{api_base}/assets/sync/runs/{run_id}",
                headers=auth_headers,
                params={"include_changes": True, "changes_limit": 50},
                expected=(200,),
            )
        )

    # 7) Tools（只做读取，避免污染）
    results.append(
        request_json(
            name="工具定义列表",
            method="GET",
            url=f"{api_base}/tools/definitions",
            headers=auth_headers,
            expected=(200,),
        )
    )
    results.append(
        request_json(
            name="工具执行记录",
            method="GET",
            url=f"{api_base}/tools/executions",
            headers=auth_headers,
            expected=(200,),
        )
    )
    results.append(
        request_json(
            name="代码目录列表",
            method="GET",
            url=f"{api_base}/code/directories",
            headers=auth_headers,
            expected=(200,),
        )
    )
    results.append(
        request_json(
            name="脚本仓库列表",
            method="GET",
            url=f"{api_base}/tools/repositories",
            headers=auth_headers,
            expected=(200,),
        )
    )
    results.append(
        request_json(
            name="脚本插件列表",
            method="GET",
            url=f"{api_base}/tools/script-plugins",
            headers=auth_headers,
            expected=(200,),
        )
    )

    print("\n=== 验证结果 ===")
    for r in results:
        _print_result(r)

    failed = [r for r in results if not r.ok]
    print("\n=== 汇总 ===")
    print(f"总计 {len(results)} 项，通过 {len(results) - len(failed)} 项，失败 {len(failed)} 项。")
    if failed:
        print("失败项：")
        for r in failed:
            print(f"- {r.name} ({r.method} {r.url}) -> {r.detail}")
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
