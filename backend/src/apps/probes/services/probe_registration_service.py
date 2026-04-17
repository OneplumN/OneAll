from __future__ import annotations

import secrets
from typing import Tuple

from django.conf import settings
from django.utils import timezone

from apps.probes.models import ProbeNode


def _generate_token(length: int = 48) -> str:
    # URL-safe strong token, truncated to requested length.
    return secrets.token_urlsafe(length)[:length]


def _get_bootstrap_token() -> str | None:
    # Bootstrap token is kept in settings to avoid leaking via database.
    return getattr(settings, "PROBE_BOOTSTRAP_TOKEN", None)


def validate_bootstrap_token(candidate: str) -> None:
    expected = _get_bootstrap_token()
    # 开发环境：如果未配置 PROBE_BOOTSTRAP_TOKEN，则不强制校验，引导 token 逻辑关闭。
    if not expected:
        return
    if not candidate or candidate != expected:
        from rest_framework.exceptions import PermissionDenied  # lazy import
        raise PermissionDenied("Invalid probe bootstrap token")


def register_probe(payload: dict) -> Tuple[ProbeNode, str]:
    """
    Create or reuse a ProbeNode for a registering agent and return node + api_token.

    注册策略（简单版本）：
    - 优先尝试通过 hostname + ip_address 复用现有节点；
    - 否则创建新节点；
    - 每次注册都会生成新的 api_token 覆盖旧值。
    """

    hostname: str = payload.get("hostname") or ""
    ip_address: str | None = payload.get("ip_address")
    location: str = (payload.get("location") or "").strip() or "自动注册"
    network_type: str = payload.get("network_type") or "external"
    supported_protocols = payload.get("supported_protocols") or []

    # 简单的复用策略：同 hostname + ip 视作同一节点。
    probe: ProbeNode | None = None
    if hostname:
        qs = ProbeNode.objects.filter(name=hostname)
        if ip_address:
            qs = qs.filter(runtime_metrics__ip_address=ip_address)
        probe = qs.first()

    if probe is None:
        probe = ProbeNode.objects.create(
            name=hostname or f"probe-{timezone.now().strftime('%Y%m%d%H%M%S')}",
            location=location,
            network_type=network_type,
            supported_protocols=supported_protocols,
            status="offline",
        )

    # 生成新的 API token 并保存 hint。
    token = _generate_token()
    probe.set_api_token(token)
    probe.touch_authenticated()

    # 将最近一次 IP 写入 runtime_metrics，方便前端展示。
    metrics = dict(probe.runtime_metrics or {})
    if ip_address:
        metrics["ip_address"] = ip_address
    metrics.setdefault("agent_version", payload.get("agent_version") or "")
    probe.runtime_metrics = metrics
    probe.save(update_fields=["runtime_metrics", "updated_at"])

    return probe, token
