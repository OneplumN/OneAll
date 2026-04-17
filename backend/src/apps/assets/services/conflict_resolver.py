from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from typing import Any

from django.db import transaction
from django.db.models import Count

from apps.assets.models import AssetRecord


@dataclass
class AssetConflictResolver:
    """Detect and mark conflicting asset records for manual review."""

    actor: Any | None = None

    def _mark(self, record: AssetRecord, status: str, details: dict[str, Any]) -> None:
        metadata = record.metadata or {}
        metadata.setdefault("conflict_log", []).append(details)
        record.sync_status = status
        record.metadata = metadata
        record.save(update_fields=["sync_status", "metadata", "updated_at"])

    @transaction.atomic
    def resolve(self) -> dict[str, Any]:
        summary: dict[str, Any] = {"conflicts": 0, "canonical_conflicts": 0, "needs_review": 0}

        # 1. 严格的“技术重复”：同一 source + external_id 出现多条记录
        duplicates = (
            AssetRecord.objects.values("source", "external_id")
            .annotate(total=Count("id"))
            .filter(total__gt=1)
        )

        for group in duplicates:
            records = list(
                AssetRecord.objects.filter(
                    source=group["source"], external_id=group["external_id"]
                ).order_by("-synced_at")
            )
            anchor = records[0]
            conflict_ids = [str(record.id) for record in records[1:]]
            for record in records[1:]:
                self._mark(
                    record,
                    "conflict",
                    {
                        "type": "duplicate",
                        "anchor": str(anchor.id),
                        "duplicates": conflict_ids,
                    },
                )
                summary["conflicts"] += 1

        # 2. 业务维度冲突：相同 asset_type + canonical_key 的多条记录
        canonical_duplicates = (
            AssetRecord.objects.exclude(asset_type="")
            .exclude(canonical_key="")
            .values("asset_type", "canonical_key")
            .annotate(total=Count("id"))
            .filter(total__gt=1)
        )

        for group in canonical_duplicates:
            records = list(
                AssetRecord.objects.filter(
                    asset_type=group["asset_type"], canonical_key=group["canonical_key"]
                ).order_by("-synced_at")
            )
            if len(records) < 2:
                continue

            anchor = records[0]
            conflicts = records[1:]
            conflict_ids = [str(record.id) for record in conflicts]
            sources = sorted({str(record.source) for record in records})

            for record in conflicts:
                self._mark(
                    record,
                    "conflict",
                    {
                        "type": "canonical_duplicate",
                        "asset_type": group["asset_type"],
                        "canonical_key": group["canonical_key"],
                        "anchor": str(anchor.id),
                        "duplicates": conflict_ids,
                        "sources": sources,
                    },
                )
                summary["conflicts"] += 1
                summary["canonical_conflicts"] += 1

        # 3. 字段缺失：名称为空的记录标记为待人工检查
        incomplete_records = AssetRecord.objects.filter(
            sync_status__in=["unknown", "synced"],
        ).filter(name__exact="")
        for record in incomplete_records:
            self._mark(
                record,
                "needs_review",
                {
                    "type": "missing_fields",
                    "fields": [
                        field
                        for field in ["name", "system_name"]
                        if not getattr(record, field)
                    ],
                },
            )
            summary["needs_review"] += 1

        return summary
