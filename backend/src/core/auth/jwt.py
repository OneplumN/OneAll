from __future__ import annotations

import datetime as dt
from functools import wraps
from typing import Any, Callable

import jwt
from django.conf import settings
from django.contrib.auth import get_user_model
from django.http import HttpRequest
from rest_framework import authentication, exceptions

from apps.core.roles import get_primary_role

User = get_user_model()

DEFAULT_ACCESS_TOKEN_TTL_SECONDS = 86400


class JWTAuthentication(authentication.BaseAuthentication):
    """Simple JWT bearer authentication for API requests."""

    keyword = "Bearer"

    def authenticate_header(self, request: HttpRequest) -> str:
        # Returning a header value enables DRF to respond with 401 (instead of 403)
        # when authentication is required but missing/invalid.
        return self.keyword

    def authenticate(self, request: HttpRequest) -> tuple[Any, None] | None:
        header = authentication.get_authorization_header(request).decode()
        if not header:
            return None
        parts = header.split()
        if len(parts) != 2 or parts[0] != self.keyword:
            raise exceptions.AuthenticationFailed("Invalid authorization header")

        token = parts[1]
        payload = decode_access_token(token)
        try:
            user = User.objects.get(id=payload["sub"])
        except User.DoesNotExist as exc:  # type: ignore[attr-defined]
            raise exceptions.AuthenticationFailed("User not found") from exc

        return user, None


def generate_access_token(user: Any, expires_in: int | None = None) -> str:
    ttl_seconds = expires_in
    if ttl_seconds is None:
        ttl_seconds = int(getattr(settings, "JWT_ACCESS_TOKEN_TTL_SECONDS", DEFAULT_ACCESS_TOKEN_TTL_SECONDS))
    now = dt.datetime.utcnow()
    payload = {
        "iss": "oneall-platform",
        "sub": str(user.id),
        "iat": now,
        "exp": now + dt.timedelta(seconds=ttl_seconds),
        "roles": sorted(_user_roles(user)),
    }
    return jwt.encode(payload, settings.SECRET_KEY, algorithm="HS256")


def decode_access_token(token: str) -> dict[str, Any]:
    try:
        return jwt.decode(token, settings.SECRET_KEY, algorithms=["HS256"])
    except jwt.PyJWTError as exc:  # pragma: no cover - thin wrapper
        raise exceptions.AuthenticationFailed("Invalid token") from exc


def decode_access_token_without_validation(token: str) -> dict[str, Any]:
    """Utility helper for debugging or internal tooling."""

    return jwt.decode(token, options={"verify_signature": False})


def require_roles(*role_names: str) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
    def decorator(view_func: Callable[..., Any]) -> Callable[..., Any]:
        @wraps(view_func)
        def wrapper(request: HttpRequest, *args: Any, **kwargs: Any) -> Any:
            if not hasattr(request, "user") or request.user.is_anonymous:
                raise exceptions.PermissionDenied("Authentication required")

            user_roles = _user_roles(request.user)
            if not set(role_names).issubset(user_roles):
                raise exceptions.PermissionDenied("Insufficient role permissions")
            return view_func(request, *args, **kwargs)

        return wrapper

    return decorator


def _user_roles(user: Any) -> set[str]:
    role = get_primary_role(user)
    if not role:
        return set()
    return {role.name}
