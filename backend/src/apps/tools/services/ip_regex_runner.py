from __future__ import annotations

import hashlib
from dataclasses import dataclass
from typing import Any, Callable, Dict

from django.conf import settings

from apps.tools.models import CodeRepositoryVersion, ScriptPlugin


class IPRegexScriptError(RuntimeError):
    """Raised when the IP regex script cannot be loaded or executed."""


@dataclass
class IPRegexRuntime:
    ip_to_regex: Callable[[list[str]], tuple[str, list[str]]]
    regex_to_ips: Callable[[str, int], list[str]]
    conversion_error: type[Exception]
    too_complex_error: type[Exception]
    max_results: int


_COMPILED_CACHE: Dict[str, IPRegexRuntime] = {}


def _load_repository_source() -> str:
    plugin_slug = getattr(settings, "IP_REGEX_PLUGIN_SLUG", "ip-regex-helper")
    plugin = (
        ScriptPlugin.objects.select_related("repository", "repository__latest_version", "repository_version")
        .filter(slug=plugin_slug, is_enabled=True, is_active=True)
        .first()
    )
    if plugin is None:
        raise IPRegexScriptError("未找到 IP 正则插件绑定，请在代码管理中注册脚本插件。")

    repository = plugin.repository
    if repository is None or not repository.is_active:
        raise IPRegexScriptError("IP 正则插件未绑定有效的脚本仓库。")

    version: CodeRepositoryVersion | None = plugin.repository_version or repository.latest_version
    if version is None:
        raise IPRegexScriptError("脚本仓库尚无发布版本，请先创建版本。")

    content = version.content or ""
    if not content.strip():
        raise IPRegexScriptError("IP 正则脚本内容为空，请在代码管理中更新脚本。")
    return content


def load_ip_regex_runtime() -> IPRegexRuntime:
    """Compile the latest IP regex script stored in the code repository."""

    source = _load_repository_source()
    fingerprint = hashlib.sha256(source.encode("utf-8")).hexdigest()
    if fingerprint in _COMPILED_CACHE:
        return _COMPILED_CACHE[fingerprint]

    namespace: dict[str, Any] = {}
    try:
        exec(source, namespace)  # noqa: S102 - script来自受信任的代码管理
    except Exception as exc:  # pragma: no cover - defensive
        raise IPRegexScriptError(f"IP 正则脚本执行失败: {exc}") from exc

    if "ip_to_regex" not in namespace or "regex_to_ips" not in namespace:
        raise IPRegexScriptError("脚本中缺少 ip_to_regex 或 regex_to_ips 函数。")

    runtime = IPRegexRuntime(
        ip_to_regex=namespace["ip_to_regex"],
        regex_to_ips=namespace["regex_to_ips"],
        conversion_error=namespace.get("RegexConversionError", RuntimeError),
        too_complex_error=namespace.get("RegexTooComplexError", RuntimeError),
        max_results=int(namespace.get("MAX_REVERSE_RESULTS", getattr(settings, "IP_REGEX_MAX_RESULTS", 2000))),
    )

    # 清理旧缓存，确保最新脚本立即生效
    _COMPILED_CACHE.clear()
    _COMPILED_CACHE[fingerprint] = runtime
    return runtime


__all__ = ["IPRegexRuntime", "IPRegexScriptError", "load_ip_regex_runtime"]
