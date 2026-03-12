from __future__ import annotations

import logging
from datetime import datetime
from typing import Any, Mapping

logger = logging.getLogger(__name__)


def record_monitoring_source_snapshot(
    *,
    source_type: str,
    payload: Mapping[str, Any],
    synced_at: datetime,
) -> None:
    """Persist monitoring source snapshot to TimescaleDB (placeholder implementation).

    真正的实现会把监控源健康结果写入 TimescaleDB，以便后续做趋势分析。
    目前先将信息记录到日志，模拟持久化行为。
    """

    logger.info(
        "monitoring_source_snapshot",
        extra={
            "source_type": source_type,
            "synced_at": synced_at.isoformat(),
            "payload": dict(payload),
        },
    )
