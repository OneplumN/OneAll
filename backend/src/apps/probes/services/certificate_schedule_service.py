from __future__ import annotations

from typing import Iterable

from django.db import transaction

from apps.alerts.services import ensure_schedule_for_probe_schedule
from apps.probes.models import ProbeSchedule


def _iter_certificate_schedules_for_target(parent: ProbeSchedule) -> Iterable[ProbeSchedule]:
  """
  Return all manual CERTIFICATE schedules that should be considered
  "paired" with the given HTTPS schedule.

  Association rule:
    - 手工调度 (source_type=MANUAL)
    - 协议为 CERTIFICATE
    - target 相同
    - 不挂在 MonitoringRequest / MonitoringJob 上
  """
  return ProbeSchedule.objects.filter(
      source_type=ProbeSchedule.Source.MANUAL,
      protocol="CERTIFICATE",
      target=parent.target,
      monitoring_request__isnull=True,
      monitoring_job__isnull=True,
  )


@transaction.atomic
def sync_certificate_schedule_for_https(parent: ProbeSchedule) -> None:
  """
  Ensure that a manual HTTPS schedule has a matching CERTIFICATE schedule
  when证书检测被启用；关闭时则暂停对应的 CERTIFICATE 调度。

  - 仅对手工调度 (source_type=MANUAL) 且 protocol=HTTPS 生效
  - 配置来源：
      parent.metadata.cert_check_enabled: bool
      parent.metadata.cert_warning_days: int
  - CERTIFICATE 调度的 metadata 将包含：
      {
        "timeout_seconds": <copy from parent>,
        "cert_check_enabled": true/false,
        "cert_warning_days": <warning_days>,
        "config": {
          "warning_threshold_days": <warning_days>,
          "timeout_seconds": <copy from parent>
        }
      }
  """
  if parent.source_type != ProbeSchedule.Source.MANUAL:
      return
  if parent.protocol != "HTTPS":
      return

  meta = parent.metadata or {}
  enabled = bool(meta.get("cert_check_enabled"))
  warning_days = int(meta.get("cert_warning_days") or 30)
  timeout_seconds = meta.get("timeout_seconds")

  cert_schedules = list(_iter_certificate_schedules_for_target(parent))

  if not enabled:
      # 关闭证书检测：暂停所有相关 CERTIFICATE 调度，但保留记录
      for cert in cert_schedules:
          if cert.status != ProbeSchedule.Status.PAUSED:
              cert.pause("证书检测已在主 HTTPS 策略中关闭")
          # 同步 metadata 标记
          cm = dict(cert.metadata or {})
          cm["cert_check_enabled"] = False
          cert.metadata = cm
          cert.save(update_fields=["metadata", "updated_at"])
      return

  # 启用证书检测
  if not cert_schedules:
      # 创建一条新的 CERTIFICATE 调度
      cert = ProbeSchedule.objects.create(
          name=f"{parent.name} / 证书检测",
          description=parent.description,
          target=parent.target,
          protocol="CERTIFICATE",
          frequency_minutes=parent.frequency_minutes,
          start_at=parent.start_at,
          end_at=parent.end_at,
          status=parent.status,
          status_reason="",
          source_type=ProbeSchedule.Source.MANUAL,
          source_id=None,
          monitoring_request=None,
          monitoring_job=None,
          metadata={
              "timeout_seconds": timeout_seconds,
              "cert_check_enabled": True,
              "cert_warning_days": warning_days,
              "config": {
                  "warning_threshold_days": warning_days,
                  "timeout_seconds": timeout_seconds,
              },
          },
      )
      # 继承探针绑定
      cert.probes.set(parent.probes.all())
      ensure_schedule_for_probe_schedule(cert)
      return

  # 已存在 CERTIFICATE 调度：同步配置
  for cert in cert_schedules:
      updated = False
      if cert.frequency_minutes != parent.frequency_minutes:
          cert.frequency_minutes = parent.frequency_minutes
          updated = True
      if cert.start_at != parent.start_at:
          cert.start_at = parent.start_at
          updated = True
      if cert.end_at != parent.end_at:
          cert.end_at = parent.end_at
          updated = True
      if cert.status != parent.status:
          cert.status = parent.status
          cert.status_reason = ""
          updated = True

      # 继承探针绑定
      parent_probe_ids = list(parent.probes.values_list("id", flat=True))
      if parent_probe_ids:
          cert.probes.set(parent_probe_ids)

      cm = dict(cert.metadata or {})
      if cm.get("timeout_seconds") != timeout_seconds:
          cm["timeout_seconds"] = timeout_seconds
          updated = True
      if cm.get("cert_check_enabled") is not True:
          cm["cert_check_enabled"] = True
          updated = True
      if cm.get("cert_warning_days") != warning_days:
          cm["cert_warning_days"] = warning_days
          updated = True
      config = dict(cm.get("config") or {})
      if config.get("warning_threshold_days") != warning_days:
          config["warning_threshold_days"] = warning_days
          updated = True
      if config.get("timeout_seconds") != timeout_seconds:
          config["timeout_seconds"] = timeout_seconds
          updated = True
      cm["config"] = config

      if updated:
          cert.metadata = cm
          cert.save(update_fields=["frequency_minutes", "start_at", "end_at", "status", "status_reason", "metadata", "updated_at"])
          ensure_schedule_for_probe_schedule(cert)

