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
        summary = {"conflicts": 0, "needs_review": 0}

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
