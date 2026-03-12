from __future__ import annotations

from collections import Counter, defaultdict
from dataclasses import dataclass
from typing import Any, Dict, Iterable, List, Mapping, Tuple

from django.utils import timezone
from rest_framework import permissions
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.assets.models import AssetRecord


def _safe_str(value: Any) -> str:
    if value is None:
        return ""
    return str(value).strip()


def _normalize_ip(value: Any) -> str:
    return _safe_str(value)


def _as_list(value: Any) -> List[Any]:
    if value is None:
        return []
    if isinstance(value, list):
        return value
    return [value]


def _extract_primary_ip(metadata: Mapping[str, Any]) -> str:
    ip = _normalize_ip(metadata.get("ip") or metadata.get("host_ip") or metadata.get("primary_ip"))
    if ip:
        return ip
    primary = metadata.get("primary_interface")
    if isinstance(primary, dict):
        ip = _normalize_ip(primary.get("ip"))
        if ip:
            return ip
    interfaces = metadata.get("interfaces")
    if isinstance(interfaces, list):
        for interface in interfaces:
            if isinstance(interface, dict):
                ip = _normalize_ip(interface.get("ip"))
                if ip:
                    return ip
    return ""


def _extract_proxy(metadata: Mapping[str, Any]) -> str:
    proxy = _safe_str(metadata.get("proxy") or metadata.get("proxy_name"))
    if proxy:
        return proxy
    proxy_hostid = _safe_str(metadata.get("proxy_hostid"))
    if proxy_hostid:
        return f"proxy_hostid:{proxy_hostid}"
    return "未分配"


def _extract_interface_availability(metadata: Mapping[str, Any]) -> str:
    value = metadata.get("interface_available_label")
    if value is None:
        value = metadata.get("interface_available")
    text = _safe_str(value)
    if text:
        return text
    return "未知"


def _extract_host_groups(metadata: Mapping[str, Any]) -> List[str]:
    groups = metadata.get("host_groups") or metadata.get("groups") or []
    result: List[str] = []
    for item in _as_list(groups):
        if isinstance(item, str):
            name = item.strip()
        elif isinstance(item, dict):
            name = _safe_str(item.get("name"))
        else:
            name = _safe_str(item)
        if name:
            result.append(name)
    return result


def _display_ipmp_system(record: Mapping[str, Any]) -> Tuple[str, str, str, str]:
    metadata = record.get("metadata") or {}
    if not isinstance(metadata, dict):
        metadata = {}
    app_name_cn = _safe_str(metadata.get("app_name_cn") or record.get("name") or record.get("system_name"))
    app_name_en = _safe_str(metadata.get("app_name_en"))
    app_code = _safe_str(metadata.get("app_code") or record.get("external_id"))
    display = app_name_cn
    if app_name_en:
        display = f"{app_name_cn}-{app_name_en}"
    # 口径：Zabbix 主机群组名称与 IPMP 系统名称一致（中文名-英文名拼接）。
    match_key = display
    return display, app_name_cn, app_name_en, app_code


def _normalize_system_key(value: Any) -> str:
    return _safe_str(value).replace("—", "-").replace("－", "-")


def _build_system_key_candidates(display: str, cn: str, en: str) -> List[str]:
    candidates = [
        _normalize_system_key(display),
        _normalize_system_key(cn),
        _normalize_system_key(en),
    ]
    return [item for item in candidates if item]


@dataclass(frozen=True)
class _CounterSummary:
    total: int
    matched: int
    missing: int
    conflicts: int


class AssetGovernanceOverviewView(APIView):
    """
    运维资产治理统计（MVP）：
    - IPMP 系统监控覆盖率（按 Zabbix 主机群组匹配 IPMP 中文名）
    - 工单台账主机 vs Zabbix 主机（按 IP 对齐）
    - Zabbix Proxy 维度主机数量与可用性
    """

    permission_classes = [permissions.IsAuthenticated]

    DEFAULT_LIMIT = 50

    def get(self, request: Request) -> Response:
        limit = self._parse_limit(request.query_params.get("limit"))

        ipmp_records = list(
            AssetRecord.objects.filter(source=AssetRecord.Source.IPMP).values(
                "external_id",
                "name",
                "system_name",
                "metadata",
            )
        )
        zabbix_records = list(
            AssetRecord.objects.filter(source=AssetRecord.Source.ZABBIX).values(
                "external_id",
                "name",
                "metadata",
            )
        )
        workorder_records = list(
            AssetRecord.objects.filter(source=AssetRecord.Source.MANUAL).values(
                "external_id",
                "name",
                "system_name",
                "metadata",
            )
        )

        zabbix_by_ip, zabbix_groups, proxy_stats = self._index_zabbix(zabbix_records)
        workorder_by_ip, workorder_systems = self._index_workorder(workorder_records)

        ip_reconcile = self._build_ip_reconcile(workorder_by_ip, zabbix_by_ip, limit=limit)
        zabbix_coverage = self._build_zabbix_ipmp_coverage(ipmp_records, zabbix_groups, limit=limit)
        ledger_coverage = self._build_ledger_ipmp_coverage(ipmp_records, workorder_systems, limit=limit)
        matrix = self._build_coverage_matrix(ipmp_records, workorder_systems, zabbix_groups, limit=limit)

        payload = {
            "generated_at": timezone.now().isoformat(),
            "summary": {
                "ipmp_total": len(ipmp_records),
                "zabbix_host_total": len(zabbix_records),
                "workorder_host_total": len(workorder_by_ip),
            },
            # 兼容字段：历史前端使用 ipmp_coverage 表示“Zabbix 覆盖”
            "ipmp_coverage": zabbix_coverage,
            "zabbix_coverage": zabbix_coverage,
            # 兼容字段：历史前端使用 ledger_coverage 表示“工单覆盖”
            "ledger_coverage": ledger_coverage,
            "workorder_coverage": ledger_coverage,
            "coverage_matrix": matrix,
            "ip_reconcile": ip_reconcile,
            # proxy 通常数量不大，直接返回全量，前端自行做 topN/筛选即可。
            "proxy_stats": proxy_stats,
        }
        return Response(payload)

    @classmethod
    def _parse_limit(cls, value: Any) -> int:
        try:
            parsed = int(value)
        except (TypeError, ValueError):
            return cls.DEFAULT_LIMIT
        return max(1, min(parsed, 500))

    @staticmethod
    def _index_zabbix(records: Iterable[Mapping[str, Any]]):
        by_ip: dict[str, list[dict[str, Any]]] = defaultdict(list)
        groups: set[str] = set()
        proxy_counter: dict[str, Counter] = defaultdict(Counter)

        for record in records:
            metadata = record.get("metadata") or {}
            if not isinstance(metadata, dict):
                metadata = {}
            ip = _extract_primary_ip(metadata)
            if ip:
                by_ip[ip].append(
                    {
                        "external_id": _safe_str(record.get("external_id")),
                        "host_name": _safe_str(metadata.get("host_name") or record.get("name")),
                        "visible_name": _safe_str(metadata.get("visible_name") or record.get("name")),
                        "availability": _extract_interface_availability(metadata),
                        "proxy": _extract_proxy(metadata),
                        "groups": _extract_host_groups(metadata),
                    }
                )

            for group in _extract_host_groups(metadata):
                groups.add(group)

            proxy = _extract_proxy(metadata)
            availability = _extract_interface_availability(metadata)
            proxy_counter[proxy]["total"] += 1
            if availability in {"不可用", "offline"}:
                proxy_counter[proxy]["unavailable"] += 1
            elif availability in {"未知"}:
                proxy_counter[proxy]["unknown"] += 1
            else:
                proxy_counter[proxy]["available"] += 1

        proxy_stats = [
            {
                "proxy": proxy,
                "total": int(counter.get("total") or 0),
                "available": int(counter.get("available") or 0),
                "unavailable": int(counter.get("unavailable") or 0),
                "unknown": int(counter.get("unknown") or 0),
            }
            for proxy, counter in proxy_counter.items()
        ]
        proxy_stats.sort(key=lambda item: (item["unavailable"], item["unknown"], item["total"]), reverse=True)
        return by_ip, groups, proxy_stats

    @staticmethod
    def _index_workorder(records: Iterable[Mapping[str, Any]]) -> Tuple[dict[str, dict[str, Any]], dict[str, int]]:
        by_ip: dict[str, dict[str, Any]] = {}
        duplicates: set[str] = set()
        seen: set[str] = set()
        system_counter: Counter = Counter()

        for record in records:
            metadata = record.get("metadata") or {}
            if not isinstance(metadata, dict):
                metadata = {}
            asset_type = _safe_str(metadata.get("asset_type"))
            if asset_type and asset_type not in {"workorder-host", "workorder"}:
                continue
            ext = _safe_str(record.get("external_id"))
            if ext and not ext.startswith("workorder:") and asset_type != "workorder-host":
                # 手工资产可能混入其他类型，尽量不误判为工单台账。
                continue

            ip = _normalize_ip(metadata.get("ip"))
            if not ip:
                continue
            system_name = _normalize_system_key(metadata.get("app_system") or record.get("system_name"))
            if system_name:
                system_counter[system_name] += 1
            if ip in seen:
                duplicates.add(ip)
            seen.add(ip)
            by_ip[ip] = {
                "ip": ip,
                "hostname": _safe_str(metadata.get("hostname") or record.get("name")),
                "system_name": system_name,
                "owner": _safe_str(metadata.get("owner")),
                "proxy": _safe_str(metadata.get("proxy")),
            }

        for ip in duplicates:
            by_ip[ip]["duplicate"] = True

        return by_ip, dict(system_counter)

    @staticmethod
    def _summarize_sets(source: set[str], target: set[str]) -> _CounterSummary:
        matched = len(source & target)
        missing = len(source - target)
        conflicts = 0
        return _CounterSummary(total=len(source), matched=matched, missing=missing, conflicts=conflicts)

    @classmethod
    def _build_ip_reconcile(
        cls,
        workorder_by_ip: Mapping[str, Mapping[str, Any]],
        zabbix_by_ip: Mapping[str, List[Mapping[str, Any]]],
        *,
        limit: int,
    ) -> Dict[str, Any]:
        workorder_ips = set(workorder_by_ip.keys())
        zabbix_ips = set(zabbix_by_ip.keys())

        missing_in_zabbix = sorted(workorder_ips - zabbix_ips)
        extra_in_zabbix = sorted(zabbix_ips - workorder_ips)

        zabbix_ip_conflicts = sorted([ip for ip, hosts in zabbix_by_ip.items() if len(hosts) > 1])
        workorder_ip_conflicts = sorted([ip for ip, data in workorder_by_ip.items() if data.get("duplicate")])

        missing_details = [
            {
                "ip": ip,
                "hostname": _safe_str(workorder_by_ip.get(ip, {}).get("hostname")),
                "system_name": _safe_str(workorder_by_ip.get(ip, {}).get("system_name")),
                "owner": _safe_str(workorder_by_ip.get(ip, {}).get("owner")),
            }
            for ip in missing_in_zabbix[:limit]
        ]

        extra_details = [
            {
                "ip": ip,
                "hosts": [
                    {
                        "host_name": _safe_str(item.get("host_name")),
                        "visible_name": _safe_str(item.get("visible_name")),
                        "proxy": _safe_str(item.get("proxy")),
                        "availability": _safe_str(item.get("availability")),
                    }
                    for item in (zabbix_by_ip.get(ip) or [])[:3]
                ],
            }
            for ip in extra_in_zabbix[:limit]
        ]

        zabbix_conflict_details = [
            {
                "ip": ip,
                "hosts": [
                    {
                        "host_name": _safe_str(item.get("host_name")),
                        "visible_name": _safe_str(item.get("visible_name")),
                        "proxy": _safe_str(item.get("proxy")),
                    }
                    for item in (zabbix_by_ip.get(ip) or [])[:5]
                ],
            }
            for ip in zabbix_ip_conflicts[:limit]
        ]

        return {
            "workorder_total": len(workorder_ips),
            "zabbix_total": len(zabbix_ips),
            "matched_by_ip": len(workorder_ips & zabbix_ips),
            "missing_in_zabbix": len(missing_in_zabbix),
            "extra_in_zabbix": len(extra_in_zabbix),
            "workorder_ip_conflicts": len(workorder_ip_conflicts),
            "zabbix_ip_conflicts": len(zabbix_ip_conflicts),
            "missing_in_zabbix_items": missing_details,
            "extra_in_zabbix_items": extra_details,
            "zabbix_ip_conflict_items": zabbix_conflict_details,
        }

    @classmethod
    def _build_zabbix_ipmp_coverage(
        cls,
        ipmp_records: Iterable[Mapping[str, Any]],
        zabbix_groups: set[str],
        *,
        limit: int,
    ) -> Dict[str, Any]:
        uncovered: List[Dict[str, Any]] = []
        monitored = 0
        total = 0

        for record in ipmp_records:
            display, cn, en, app_code = _display_ipmp_system(record)
            match_key = _normalize_system_key(display)
            if not match_key:
                continue
            total += 1
            metadata = record.get("metadata") or {}
            if not isinstance(metadata, dict):
                metadata = {}

            is_monitored = match_key in zabbix_groups
            if is_monitored:
                monitored += 1
                continue

            uncovered.append(
                {
                    "display_name": display,
                    "match_key": match_key,
                    "app_code": app_code,
                    "app_status": _safe_str(metadata.get("app_status") or metadata.get("status")),
                    "owner": _safe_str(metadata.get("owner")) or _safe_str(record.get("owners")),
                    "security_level": _safe_str(metadata.get("security_level")),
                    "system_origin": _safe_str(metadata.get("system_origin")),
                }
            )

        uncovered.sort(key=lambda item: item.get("app_code") or item.get("display_name") or "")

        rate = (monitored / total) if total else 0
        return {
            "total": total,
            "monitored": monitored,
            "uncovered": total - monitored,
            "monitored_rate": round(rate, 4),
            "uncovered_items": uncovered[:limit],
        }

    @classmethod
    def _build_ledger_ipmp_coverage(
        cls,
        ipmp_records: Iterable[Mapping[str, Any]],
        workorder_systems: Mapping[str, int],
        *,
        limit: int,
    ) -> Dict[str, Any]:
        covered = 0
        total = 0
        uncovered: List[Dict[str, Any]] = []

        ledger_keys = {_normalize_system_key(key) for key in workorder_systems.keys() if _normalize_system_key(key)}

        for record in ipmp_records:
            display, cn, en, app_code = _display_ipmp_system(record)
            candidates = _build_system_key_candidates(display, cn, en)
            if not candidates:
                continue
            total += 1
            metadata = record.get("metadata") or {}
            if not isinstance(metadata, dict):
                metadata = {}

            is_covered = any(candidate in ledger_keys for candidate in candidates)
            if is_covered:
                covered += 1
                continue

            uncovered.append(
                {
                    "display_name": display,
                    "match_key": _normalize_system_key(display),
                    "app_code": app_code,
                    "app_status": _safe_str(metadata.get("app_status") or metadata.get("status")),
                    "owner": _safe_str(metadata.get("owner")) or _safe_str(record.get("owners")),
                    "security_level": _safe_str(metadata.get("security_level")),
                    "system_origin": _safe_str(metadata.get("system_origin")),
                }
            )

        uncovered.sort(key=lambda item: item.get("app_code") or item.get("display_name") or "")
        rate = (covered / total) if total else 0
        return {
            "total": total,
            "covered": covered,
            "uncovered": total - covered,
            "covered_rate": round(rate, 4),
            "uncovered_items": uncovered[:limit],
        }

    @classmethod
    def _build_coverage_matrix(
        cls,
        ipmp_records: Iterable[Mapping[str, Any]],
        workorder_systems: Mapping[str, int],
        zabbix_groups: set[str],
        *,
        limit: int,
    ) -> Dict[str, Any]:
        ledger_keys = {_normalize_system_key(key) for key in workorder_systems.keys() if _normalize_system_key(key)}
        zabbix_keys = {_normalize_system_key(key) for key in zabbix_groups if _normalize_system_key(key)}

        buckets: dict[str, list[Dict[str, Any]]] = defaultdict(list)
        counts: Counter = Counter()

        for record in ipmp_records:
            display, cn, en, app_code = _display_ipmp_system(record)
            candidates = _build_system_key_candidates(display, cn, en)
            if not candidates:
                continue
            metadata = record.get("metadata") or {}
            if not isinstance(metadata, dict):
                metadata = {}

            ledger_hit = any(candidate in ledger_keys for candidate in candidates)
            zabbix_hit = _normalize_system_key(display) in zabbix_keys

            if ledger_hit and zabbix_hit:
                key = "both"
            elif ledger_hit and not zabbix_hit:
                key = "ledger_only"
            elif (not ledger_hit) and zabbix_hit:
                key = "zabbix_only"
            else:
                key = "neither"

            counts[key] += 1
            buckets[key].append(
                {
                    "display_name": display,
                    "app_code": app_code,
                    "app_status": _safe_str(metadata.get("app_status") or metadata.get("status")),
                    "owner": _safe_str(metadata.get("owner")) or _safe_str(record.get("owners")),
                }
            )

        for key in buckets:
            buckets[key].sort(key=lambda item: item.get("app_code") or item.get("display_name") or "")

        return {
            "counts": {
                "both": int(counts.get("both") or 0),
                "ledger_only": int(counts.get("ledger_only") or 0),
                "zabbix_only": int(counts.get("zabbix_only") or 0),
                "neither": int(counts.get("neither") or 0),
            },
            "items": {
                "ledger_only": buckets.get("ledger_only", [])[:limit],
                "zabbix_only": buckets.get("zabbix_only", [])[:limit],
                "neither": buckets.get("neither", [])[:limit],
            },
        }


class AssetProxyHostsView(APIView):
    """
    按 Zabbix Proxy 查看纳管主机明细（按 IP 聚合）。
    - 口径：以 Zabbix 主机为准
    - 主键：以 IP 聚合展示（IP 冲突会在同一 IP 下展示多条主机）
    """

    permission_classes = [permissions.IsAuthenticated]

    DEFAULT_LIMIT = 50
    MAX_LIMIT = 200

    def get(self, request: Request) -> Response:
        proxy = _safe_str(request.query_params.get("proxy"))
        if not proxy:
            return Response({"detail": "proxy 不能为空"}, status=400)

        keyword = _safe_str(request.query_params.get("keyword")).lower()
        only_abnormal = _safe_str(request.query_params.get("only_abnormal")).lower() in {"1", "true", "yes", "y"}
        limit = self._parse_limit(request.query_params.get("limit"))
        offset = self._parse_offset(request.query_params.get("offset"))

        zabbix_records = list(
            AssetRecord.objects.filter(source=AssetRecord.Source.ZABBIX).values(
                "external_id",
                "name",
                "metadata",
            )
        )

        groups: dict[str, list[dict[str, Any]]] = defaultdict(list)
        abnormal_hosts = 0
        total_hosts = 0

        for record in zabbix_records:
            metadata = record.get("metadata") or {}
            if not isinstance(metadata, dict):
                metadata = {}

            record_proxy = _extract_proxy(metadata)
            if record_proxy != proxy:
                continue

            ip = _extract_primary_ip(metadata) or "无IP"
            host_name = _safe_str(metadata.get("host_name") or record.get("name"))
            visible_name = _safe_str(metadata.get("visible_name") or record.get("name"))
            availability = _extract_interface_availability(metadata)
            host_groups = _extract_host_groups(metadata)

            is_abnormal = availability in {"不可用", "未知", "offline"}

            if only_abnormal and not is_abnormal:
                continue

            if keyword:
                haystacks = [
                    ip.lower(),
                    host_name.lower(),
                    visible_name.lower(),
                    " ".join(host_groups).lower(),
                ]
                if not any(keyword in text for text in haystacks if text):
                    continue

            total_hosts += 1
            if is_abnormal:
                abnormal_hosts += 1

            groups[ip].append(
                {
                    "external_id": _safe_str(record.get("external_id")),
                    "host_name": host_name,
                    "visible_name": visible_name,
                    "availability": availability,
                    "proxy": record_proxy,
                    "groups": host_groups,
                    "is_abnormal": is_abnormal,
                }
            )

        items: list[dict[str, Any]] = []
        conflict_ip_total = 0
        no_ip_total = 0

        for ip, hosts in groups.items():
            hosts.sort(key=lambda item: item.get("host_name") or item.get("visible_name") or "")
            abnormal_count = sum(1 for host in hosts if host.get("is_abnormal"))
            if ip == "无IP":
                no_ip_total += 1
            elif len(hosts) > 1:
                conflict_ip_total += 1
            items.append(
                {
                    "ip": ip,
                    "host_count": len(hosts),
                    "abnormal_count": abnormal_count,
                    "hosts": hosts,
                }
            )

        def _item_sort_key(item: Mapping[str, Any]) -> tuple[int, str]:
            ip = _safe_str(item.get("ip"))
            if ip == "无IP":
                return (1, ip)
            return (0, ip)

        items.sort(key=_item_sort_key)

        total = len(items)
        sliced = items[offset : offset + limit]

        return Response(
            {
                "generated_at": timezone.now().isoformat(),
                "proxy": proxy,
                "summary": {
                    "host_total": total_hosts,
                    "abnormal_host_total": abnormal_hosts,
                    "ip_total": total,
                    "conflict_ip_total": conflict_ip_total,
                    "no_ip_total": no_ip_total,
                },
                "pagination": {"limit": limit, "offset": offset, "total": total},
                "items": sliced,
            }
        )

    @classmethod
    def _parse_limit(cls, value: Any) -> int:
        try:
            parsed = int(value)
        except (TypeError, ValueError):
            return cls.DEFAULT_LIMIT
        return max(1, min(parsed, cls.MAX_LIMIT))

    @staticmethod
    def _parse_offset(value: Any) -> int:
        try:
            parsed = int(value)
        except (TypeError, ValueError):
            return 0
        return max(0, parsed)
