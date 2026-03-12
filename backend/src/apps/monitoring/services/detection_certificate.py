from __future__ import annotations

import math
import socket
import ssl
from dataclasses import dataclass
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict
from urllib.parse import urlparse


class CertificateStatus(str, Enum):
    VALID = "valid"
    EXPIRES_SOON = "expires_soon"
    EXPIRED = "expired"
    ERROR = "error"


@dataclass
class CertificateReport:
    status: CertificateStatus
    days_until_expiry: int | None
    issuer: str | None = None
    subject: str | None = None
    message: str | None = None


def analyze_certificate(target: str, warning_threshold_days: int = 7) -> CertificateReport:
    try:
        cert = fetch_certificate_info(target)
    except Exception as exc:  # pragma: no cover - network failure path
        return CertificateReport(
            status=CertificateStatus.ERROR,
            days_until_expiry=None,
            message=str(exc),
        )

    not_after_str = cert.get('notAfter')
    if not not_after_str:
        return CertificateReport(
            status=CertificateStatus.ERROR,
            days_until_expiry=None,
            message='证书缺少过期时间信息',
        )

    expires_at = datetime.strptime(not_after_str, '%b %d %H:%M:%S %Y %Z').replace(tzinfo=timezone.utc)
    delta_seconds = (expires_at - datetime.now(timezone.utc)).total_seconds()
    delta = int(round(delta_seconds / 86400))

    issuer = _extract_cn(cert.get('issuer'))
    subject = _extract_cn(cert.get('subject'))

    if delta < 0:
        status = CertificateStatus.EXPIRED
    elif delta <= warning_threshold_days:
        status = CertificateStatus.EXPIRES_SOON
    else:
        status = CertificateStatus.VALID

    return CertificateReport(
        status=status,
        days_until_expiry=delta,
        issuer=issuer,
        subject=subject,
    )


def fetch_certificate_info(target: str) -> Dict[str, Any]:
    parsed = urlparse(target)
    hostname = parsed.hostname or target
    port = parsed.port or 443

    context = ssl.create_default_context()
    with socket.create_connection((hostname, port), timeout=10) as sock:
        with context.wrap_socket(sock, server_hostname=hostname) as ssock:
            return ssock.getpeercert()


def _extract_cn(name_tuple):
    if not name_tuple:
        return None
    for pair in name_tuple:
        if isinstance(pair, tuple):
            for key, value in pair:
                if key == 'commonName':
                    return value
    return None
