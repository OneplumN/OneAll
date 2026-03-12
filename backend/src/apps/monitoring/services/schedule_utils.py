from __future__ import annotations

from datetime import datetime, timedelta


def calculate_next_run(*, previous_next_run: datetime | None, interval_minutes: int, now: datetime) -> datetime:
    """Compute the next run timestamp anchored to the previous schedule slot.

    This prevents long-running tasks from drifting and keeps the cadence close to
    the configured interval even when Celery beat triggers slightly later than
    expected.
    """

    minutes = max(interval_minutes or 0, 1)
    interval = timedelta(minutes=minutes)
    reference = previous_next_run or now
    next_run = reference + interval
    while next_run <= now:
        next_run += interval
    return next_run
