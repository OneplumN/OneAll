from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from django.db.models import Q

from apps.assets.models import AssetRecord


class CMDBValidationStatus(str, Enum):
    OK = "ok"
    NOT_FOUND = "not_found"
    ERROR = "error"


@dataclass
class CMDBValidationResult:
    status: CMDBValidationStatus
    message: str | None = None
    record: dict | None = None


def validate_domain(domain: str) -> CMDBValidationResult:
    domain = (domain or "").strip()
    if not domain:
        return CMDBValidationResult(
            status=CMDBValidationStatus.ERROR,
            message="域名不能为空",
        )

    try:
        asset = (
            AssetRecord.objects.filter(
                source=AssetRecord.Source.CMDB,
                metadata__asset_type="cmdb-domain",
            )
            .filter(
                Q(metadata__domain__iexact=domain)
                | Q(name__iexact=domain)
                | Q(external_id__iexact=domain)
                | Q(external_id__iexact=f"domain:{domain}")
            )
            .order_by("-synced_at")
            .first()
        )
    except Exception as exc:  # pragma: no cover - unexpected ORM/DB failure path
        return CMDBValidationResult(
            status=CMDBValidationStatus.ERROR,
            message=str(exc),
        )

    if asset is None:
        return CMDBValidationResult(
            status=CMDBValidationStatus.NOT_FOUND,
            message="未在本地资产中找到匹配的域名，请先同步 CMDB 资产源",
            record=None,
        )

    metadata = dict(asset.metadata or {})

    system = asset.system_name or metadata.get("system") or metadata.get("system_name")
    internet_type = metadata.get("internet_type") or metadata.get("network_type")
    contacts = metadata.get("contacts") or metadata.get("alert_contacts") or asset.contacts
    owner = metadata.get("owner") or (asset.owners[0] if asset.owners else None)

    record = {
        "domain": metadata.get("domain") or asset.name,
        "system": system,
        "internet_type": internet_type,
        "owner": owner,
        "contacts": contacts,
        "status": asset.sync_status or metadata.get("status"),
        "updated_at": asset.synced_at.isoformat(),
    }

    for key, value in metadata.items():
        if key in {"asset_type", "domain", "network_type", "internet_type", "alert_contacts", "system_name", "system"}:
            continue
        if key not in record and value is not None:
            record[key] = value

    return CMDBValidationResult(
        status=CMDBValidationStatus.OK,
        record=record,
    )
