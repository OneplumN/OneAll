from __future__ import annotations

from collections import Counter
from typing import Dict

from apps.assets.models import AssetRecord


def build_coverage_metrics() -> Dict[str, int]:
    total = AssetRecord.objects.count()
    by_source = Counter(AssetRecord.objects.values_list("source", flat=True))
    return {
        "total": total,
        **{f"source_{source.lower()}": count for source, count in by_source.items()},
    }
