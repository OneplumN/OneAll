from __future__ import annotations

from celery import shared_task

from apps.analytics.services.report_service import build_detection_report


@shared_task(name="apps.analytics.tasks.export_detection_report")
def export_detection_report(days: int = 30) -> dict:
    report = build_detection_report(days=days)
    # 真实实现会将报表存储到对象存储或发送邮件，此处返回结果以便测试。
    return report
