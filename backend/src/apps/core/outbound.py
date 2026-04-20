from __future__ import annotations

import ipaddress
import socket
from urllib.parse import urlparse

from django.conf import settings


class UnsafeOutboundURLError(ValueError):
    """Raised when an outbound webhook/callback target is unsafe."""


def validate_outbound_hook_url(url: str, *, resolve_dns: bool) -> None:
    parsed = urlparse(str(url or "").strip())
    if parsed.scheme not in {"http", "https"}:
        raise UnsafeOutboundURLError("仅允许使用 http 或 https 回调地址")
    if not parsed.hostname:
        raise UnsafeOutboundURLError("回调地址缺少主机名")
    if parsed.username or parsed.password:
        raise UnsafeOutboundURLError("回调地址不允许包含用户名或密码")

    if _allow_private_outbound_hooks():
        return

    hostname = parsed.hostname.rstrip(".").lower()
    if hostname == "localhost" or hostname.endswith(".localhost"):
        raise UnsafeOutboundURLError("回调地址不能指向本机或 localhost")

    literal_ip = _parse_ip(hostname)
    if literal_ip is not None:
        _ensure_public_ip(literal_ip)
        return

    if not resolve_dns:
        return

    try:
        resolved = socket.getaddrinfo(hostname, parsed.port or _default_port_for_scheme(parsed.scheme), type=socket.SOCK_STREAM)
    except socket.gaierror as exc:
        raise UnsafeOutboundURLError("回调地址解析失败") from exc

    if not resolved:
        raise UnsafeOutboundURLError("回调地址解析失败")

    for _, _, _, _, sockaddr in resolved:
        candidate = _parse_ip(str(sockaddr[0]))
        if candidate is None:
            raise UnsafeOutboundURLError("回调地址解析结果无效")
        _ensure_public_ip(candidate)


def _allow_private_outbound_hooks() -> bool:
    return bool(getattr(settings, "ALLOW_PRIVATE_OUTBOUND_HOOK_URLS", False))


def _default_port_for_scheme(scheme: str) -> int:
    return 443 if scheme == "https" else 80


def _parse_ip(value: str) -> ipaddress.IPv4Address | ipaddress.IPv6Address | None:
    try:
        return ipaddress.ip_address(value)
    except ValueError:
        return None


def _ensure_public_ip(ip: ipaddress.IPv4Address | ipaddress.IPv6Address) -> None:
    if not ip.is_global:
        raise UnsafeOutboundURLError("回调地址不能指向内网、保留地址或本机地址")
