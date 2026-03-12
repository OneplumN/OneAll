from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Sequence

from ldap3 import Connection, Server, SUBTREE

from apps.settings.services.system_settings_service import get_integration_settings


class LDAPConfigurationError(Exception):
    """Raised when LDAP configuration is missing or invalid."""


@dataclass
class LDAPContext:
    config: Dict[str, Any]
    server: Server
    bind_kwargs: Dict[str, Any]
    base_dn: str


def authenticate_via_ldap(username: str, password: str) -> Dict[str, Any] | None:
    if not password:
        return None
    try:
        ctx = _prepare_context()
    except LDAPConfigurationError:
        return None

    user_filter = ctx.config.get("user_filter") or "(uid={username})"
    display_name_attr = ctx.config.get("display_name_attr") or "cn"
    email_attr = ctx.config.get("email_attr") or "mail"

    try:
        with Connection(ctx.server, **ctx.bind_kwargs) as conn:
            search_filter = user_filter.format(username=username)
            conn.search(
                search_base=ctx.base_dn,
                search_filter=search_filter,
                search_scope=SUBTREE,
                attributes=[display_name_attr, email_attr],
            )
            if not conn.entries:
                return None
            entry = conn.entries[0]
            user_dn = entry.entry_dn
            attributes = entry.entry_attributes_as_dict
            display_values = attributes.get(display_name_attr) or []
            email_values = attributes.get(email_attr) or []
            display_name = display_values[0] if display_values else username
            email = email_values[0] if email_values else ""
        # Verify user credentials by binding with the located DN
        with Connection(ctx.server, user=user_dn, password=password, auto_bind=True):
            pass
    except Exception:
        return None

    return {
        "dn": user_dn,
        "display_name": display_name or username,
        "email": email or "",
    }


def fetch_directory_entries(
    *, search_filter: str, attributes: Sequence[str], size_limit: int | None = None
) -> List[Dict[str, Any]]:
    ctx = _prepare_context()
    attr_list = list(dict.fromkeys(attributes))
    with Connection(ctx.server, **ctx.bind_kwargs) as conn:
        conn.search(
            search_base=ctx.base_dn,
            search_filter=search_filter,
            search_scope=SUBTREE,
            attributes=attr_list,
            size_limit=size_limit or 0,
        )
        results: List[Dict[str, Any]] = []
        for entry in conn.entries:
            attr_dict = entry.entry_attributes_as_dict
            results.append(
                {
                    "dn": entry.entry_dn,
                    "attributes": {attr: attr_dict.get(attr) or [] for attr in attr_list},
                }
            )
    return results


def _prepare_context() -> LDAPContext:
    config = get_integration_settings("ldap")
    if not config.get("enabled"):
        raise LDAPConfigurationError("LDAP 未启用")
    host = config.get("host")
    if not host:
        raise LDAPConfigurationError("LDAP 服务器地址未配置")
    port = int(config.get("port") or 389)
    use_ssl = bool(config.get("use_ssl"))
    base_dn = config.get("base_dn") or ""
    bind_dn = config.get("bind_dn") or None
    bind_password = config.get("bind_password") or None

    server = Server(host, port=port, use_ssl=use_ssl, get_info=None)
    bind_kwargs: Dict[str, Any] = {"auto_bind": True}
    if bind_dn:
        bind_kwargs.update({"user": bind_dn, "password": bind_password})
    return LDAPContext(config=config, server=server, bind_kwargs=bind_kwargs, base_dn=base_dn)
