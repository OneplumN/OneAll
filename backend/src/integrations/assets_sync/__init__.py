from __future__ import annotations

from typing import Any, Callable, Dict, Iterable, List, Sequence, Tuple

from .sources.cmdb import fetch_cmdb_domains
from .sources.zabbix import fetch_zabbix_hosts
from .sources.ipmp import fetch_ipmp_projects
from .sources.workorder import fetch_workorder_hosts
Collector = Callable[[], Sequence[Dict[str, Any]]]

COLLECTOR_REGISTRY: Tuple[Tuple[str, Collector, Tuple[str, ...]], ...] = (
    ("CMDB", fetch_cmdb_domains, ("asset_cmdb_domain",)),
    ("Zabbix", fetch_zabbix_hosts, ("asset_zabbix_host",)),
    ("IPMP", fetch_ipmp_projects, ("asset_ipmp_project",)),
    ("Manual", fetch_workorder_hosts, ("asset_workorder_host", "Workorder")),
)


def collect_sources(source_filters: Iterable[str] | None = None) -> List[Dict[str, Any]]:
    """
    Collect asset records from configured sources.

    :param source_filters: Optional iterable of source names or plugin keys to include.
    """

    normalized_filters = {value.strip().lower() for value in source_filters or [] if str(value).strip()}
    records: List[Dict[str, Any]] = []

    for source_name, collector, aliases in COLLECTOR_REGISTRY:
        keys = {source_name.lower(), *(alias.lower() for alias in aliases)}
        if normalized_filters and normalized_filters.isdisjoint(keys):
            continue
        records.extend(collector())
    return records


def collect_all_sources() -> List[Dict[str, Any]]:
    return collect_sources()


__all__ = [
    "collect_all_sources",
    "collect_sources",
]
