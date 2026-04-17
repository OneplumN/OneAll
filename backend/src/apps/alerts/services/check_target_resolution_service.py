from __future__ import annotations

import re
from dataclasses import dataclass
from ipaddress import ip_address
from typing import Optional
from uuid import UUID
from urllib.parse import urlparse

from django.db.models import Q

from apps.alerts.models import AlertCheck
from apps.assets.models import AssetRecord

DOMAIN_LABEL_PATTERN = re.compile(r"^[a-z0-9-]+$")

MATCHED = "matched"
MISSING_SYSTEM = "missing_system"
UNMANAGED = "unmanaged"
INVALID_TARGET = "invalid_target"


@dataclass(frozen=True)
class ResolutionResult:
    resolved_domain: str
    resolved_system_name: str
    asset_record_id: Optional[UUID]
    asset_match_status: str


def normalize_target_to_domain(target: str) -> str | None:
    raw_target = (target or "").strip()
    if not raw_target:
        return None

    parsed = urlparse(raw_target if "://" in raw_target else f"//{raw_target}")
    hostname = parsed.hostname
    if hostname:
        candidate = hostname
    else:
        candidate = (
            raw_target.split("/", 1)[0]
            .split("?", 1)[0]
            .split("#", 1)[0]
            .strip()
        )
        if ":" in candidate:
            reparsed = urlparse(f"//{candidate}")
            candidate = reparsed.hostname or candidate.split(":", 1)[0]

    normalized = candidate.strip().lower().rstrip(".")
    if not normalized or " " in normalized:
        return None

    try:
        ip_address(normalized)
    except ValueError:
        pass
    else:
        return None

    labels = normalized.split(".")
    if len(labels) < 2:
        return None
    for label in labels:
        if not label or len(label) > 63:
            return None
        if label.startswith("-") or label.endswith("-"):
            return None
        if not DOMAIN_LABEL_PATTERN.match(label):
            return None

    return normalized


def resolve_check_target(target: str) -> ResolutionResult:
    raw_target = (target or "").strip()
    resolved_domain = normalize_target_to_domain(raw_target)
    if not resolved_domain:
        return ResolutionResult(
            resolved_domain="",
            resolved_system_name="",
            asset_record_id=None,
            asset_match_status=INVALID_TARGET,
        )

    target_variants = _build_target_variants(raw_target, resolved_domain)

    asset = (
        AssetRecord.objects.filter(
            Q(asset_type__iexact="cmdb-domain")
            | Q(metadata__asset_type="cmdb-domain")
        )
        .filter(
            _build_target_lookup(target_variants)
        )
        .order_by("-synced_at", "-created_at")
        .first()
    )

    if asset is None:
        return ResolutionResult(
            resolved_domain=resolved_domain,
            resolved_system_name="",
            asset_record_id=None,
            asset_match_status=UNMANAGED,
        )

    resolved_system_name = (asset.system_name or "").strip()
    return ResolutionResult(
        resolved_domain=resolved_domain,
        resolved_system_name=resolved_system_name,
        asset_record_id=asset.id,
        asset_match_status=MATCHED if resolved_system_name else MISSING_SYSTEM,
    )


def apply_resolution_snapshot(check: AlertCheck) -> AlertCheck:
    result = resolve_check_target(check.target)
    update_fields: list[str] = []

    if check.resolved_domain != result.resolved_domain:
        check.resolved_domain = result.resolved_domain
        update_fields.append("resolved_domain")
    if check.resolved_system_name != result.resolved_system_name:
        check.resolved_system_name = result.resolved_system_name
        update_fields.append("resolved_system_name")
    if check.asset_record_id != result.asset_record_id:
        check.asset_record_id = result.asset_record_id
        update_fields.append("asset_record_id")
    if check.asset_match_status != result.asset_match_status:
        check.asset_match_status = result.asset_match_status
        update_fields.append("asset_match_status")

    if update_fields:
        update_fields.append("updated_at")
        check.save(update_fields=update_fields)

    return check


def _build_target_variants(raw_target: str, resolved_domain: str) -> list[str]:
    variants: list[str] = []
    for value in {
        raw_target.strip(),
        raw_target.strip().rstrip("/"),
        resolved_domain,
        f"domain:{resolved_domain}",
    }:
        cleaned = (value or "").strip()
        if cleaned:
            variants.append(cleaned)
    return variants


def _build_target_lookup(variants: list[str]) -> Q:
    query = Q()
    for value in variants:
        query |= (
            Q(canonical_key__iexact=value)
            | Q(metadata__domain__iexact=value)
            | Q(name__iexact=value)
            | Q(external_id__iexact=value)
        )
    return query
