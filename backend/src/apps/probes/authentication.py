from __future__ import annotations

from rest_framework.exceptions import AuthenticationFailed

from apps.probes.models import ProbeNode

HEADER_PREFIX = "probetoken"


def extract_probe_token(request) -> str | None:
    auth_header = request.META.get("HTTP_AUTHORIZATION", "")
    if isinstance(auth_header, str) and auth_header.lower().startswith(HEADER_PREFIX):
        parts = auth_header.split(None, 1)
        if len(parts) == 2:
            return parts[1].strip()
    token = request.META.get("HTTP_X_PROBE_TOKEN")
    if isinstance(token, str):
        token = token.strip()
        if token:
            return token
    return None


def ensure_probe_authenticated(request, probe: ProbeNode, token: str | None = None) -> str:
    token = token or extract_probe_token(request)
    if not token or not probe.check_api_token(token):
        raise AuthenticationFailed("Invalid probe token")
    probe.touch_authenticated()
    return token
