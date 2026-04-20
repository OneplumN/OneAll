from __future__ import annotations

from rest_framework.throttling import SimpleRateThrottle


class LoginIPThrottle(SimpleRateThrottle):
    scope = "login_ip"

    def get_cache_key(self, request, view):
        ident = self.get_ident(request)
        if not ident:
            return None
        return self.cache_format % {"scope": self.scope, "ident": ident}


class LoginUsernameThrottle(SimpleRateThrottle):
    scope = "login_username"

    def get_cache_key(self, request, view):
        username = str((request.data or {}).get("username") or "").strip().lower()
        if not username:
            username = "anonymous"
        return self.cache_format % {"scope": self.scope, "ident": username}
