from __future__ import annotations

from datetime import timedelta

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone

from apps.assets.models import AssetRecord
from apps.core.models import AuditLog
from apps.monitoring.models import DetectionTask, MonitoringJob, MonitoringRequest
from apps.probes.models import ProbeNode
from apps.settings.models import PluginConfig
from apps.tools.services.script_repository import ScriptRepositoryService
from apps.tools.models import ScriptVersion, ToolDefinition
from apps.knowledge.models import KnowledgeArticle


class Command(BaseCommand):
    help = "Seed demo data to showcase OneAll portal pages."

    demo_flag = {"demo": True}

    @transaction.atomic
    def handle(self, *args, **options):
        self.stdout.write("Seeding demo data...")

        admin_user = self._ensure_demo_user()
        probes = self._ensure_probes(admin_user)
        requests = self._ensure_monitoring_requests(admin_user)
        jobs = self._ensure_monitoring_jobs(requests, admin_user)
        self._ensure_detection_tasks(probes, jobs, admin_user)
        self._ensure_plugin_configs(admin_user)
        self._ensure_assets(admin_user)
        self._ensure_audit_logs(admin_user)
        self._ensure_tools_and_knowledge(admin_user)

        self.stdout.write(self.style.SUCCESS("Demo data ready."))

    def _ensure_demo_user(self):
        User = get_user_model()
        user, created = User.objects.get_or_create(
            username="demo-admin",
            defaults={
                "email": "demo-admin@example.com",
                "display_name": "演示管理员",
                "is_staff": True,
                "is_superuser": False,
            },
        )
        if created or not user.has_usable_password():
            user.set_password("Demo@1234")
            user.save(update_fields=["password"])
            self.stdout.write(" - 创建演示用户 demo-admin / Demo@1234")
        else:
            self.stdout.write(" - 演示用户已存在")
        return user

    def _ensure_probes(self, admin_user):
        probes = []
        probe_specs = [
            ("demo-probe-beijing-1", "北京亦庄 A 区", "internal", "online"),
            ("demo-probe-shanghai-1", "上海浦东 数据中心", "external", "online"),
            ("demo-probe-guangzhou-1", "广州天河 机房", "external", "offline"),
        ]
        for name, location, network_type, status in probe_specs:
            probe, created = ProbeNode.objects.get_or_create(
                name=name,
                defaults={
                    "location": location,
                    "network_type": network_type,
                    "status": status,
                    "supported_protocols": ["HTTP", "HTTPS", "Telnet"],
                    "created_by": admin_user,
                },
            )
            probes.append(probe)
            if created:
                self.stdout.write(f" - 新增探针 {name}")
        return probes

    def _ensure_monitoring_requests(self, admin_user):
        request_specs = [
            {
                "title": "线上支付网关巡检",
                "target": "https://pay.demo.oneall.internal",
                "protocol": MonitoringRequest.Protocol.HTTPS,
                "status": MonitoringRequest.Status.APPROVED,
                "frequency_minutes": 5,
                "itsm_ticket_id": "ITSMD-20240301-001",
            },
            {
                "title": "外网 API 可用性检测",
                "target": "https://openapi.demo.oneall.com/health",
                "protocol": MonitoringRequest.Protocol.HTTPS,
                "status": MonitoringRequest.Status.APPROVED,
                "frequency_minutes": 10,
                "itsm_ticket_id": "ITSMD-20240301-002",
            },
            {
                "title": "证书到期提醒",
                "target": "https://portal.demo.oneall.com",
                "protocol": MonitoringRequest.Protocol.CERTIFICATE,
                "status": MonitoringRequest.Status.PENDING,
                "frequency_minutes": 60,
                "itsm_ticket_id": "ITSMD-20240302-003",
            },
        ]

        requests = []
        for spec in request_specs:
            request, created = MonitoringRequest.objects.get_or_create(
                title=spec["title"],
                defaults={
                    **spec,
                    "metadata": {"demo": True, "owner": "运维平台"},
                    "created_by": admin_user,
                },
            )
            requests.append(request)
            if created:
                self.stdout.write(f" - 新增拨测申请 {spec['title']}")
        return requests

    def _ensure_monitoring_jobs(self, requests, admin_user):
        jobs = []
        for req in requests:
            if req.status != MonitoringRequest.Status.APPROVED:
                continue
            job, created = MonitoringJob.objects.get_or_create(
                request=req,
                defaults={
                    "frequency_minutes": req.frequency_minutes,
                    "status": MonitoringJob.Status.ACTIVE,
                    "metadata": {"demo": True},
                    "created_by": admin_user,
                },
            )
            jobs.append(job)
            if created:
                self.stdout.write(f" - 为 {req.title} 创建巡检任务")
        return jobs

    def _ensure_detection_tasks(self, probes, jobs, admin_user):
        DetectionTask.objects.filter(metadata__demo=True).delete()

        now = timezone.now()
        sample_tasks = [
            {
                "target": "https://pay.demo.oneall.internal",
                "protocol": DetectionTask.Protocol.HTTPS,
                "status": DetectionTask.Status.SUCCEEDED,
                "response_time_ms": 320,
                "executed_at": now - timedelta(minutes=15),
                "probe": probes[0] if probes else None,
            },
            {
                "target": "https://openapi.demo.oneall.com/health",
                "protocol": DetectionTask.Protocol.HTTPS,
                "status": DetectionTask.Status.FAILED,
                "response_time_ms": None,
                "executed_at": now - timedelta(hours=1, minutes=10),
                "probe": probes[1] if len(probes) > 1 else None,
                "error_message": "502 Bad Gateway",
            },
            {
                "target": "wss://realtime.demo.oneall.com",
                "protocol": DetectionTask.Protocol.WSS,
                "status": DetectionTask.Status.TIMEOUT,
                "response_time_ms": None,
                "executed_at": now - timedelta(hours=2, minutes=5),
                "probe": probes[2] if len(probes) > 2 else None,
                "error_message": "握手超时",
            },
        ]

        for spec in sample_tasks:
            DetectionTask.objects.create(
                target=spec["target"],
                protocol=spec["protocol"],
                status=spec["status"],
                response_time_ms=spec["response_time_ms"],
                executed_at=spec["executed_at"],
                probe=spec.get("probe"),
                metadata={"demo": True},
                result_payload={},
                error_message=spec.get("error_message", ""),
                created_by=admin_user,
                updated_by=admin_user,
            )
        self.stdout.write(" - 生成示例拨测记录 3 条")

    def _ensure_plugin_configs(self, admin_user):
        config_specs = [
            ("Zabbix 集成", "zabbix", "healthy", "Zabbix 指标同步正常", {}),
            ("Prometheus 集成", "prometheus", "degraded", "拉取延迟 5 分钟", {}),
            ("IPMP 资产同步", "ipmp", "warning", "最近一次同步失败", {}),
            (
                "CMDB 域名插件",
                "asset_cmdb_domain",
                "healthy",
                "等待下一次同步",
                {"script_command": "/opt/scripts/sync_cmdb.sh", "data_file": "/data/assets/cmdb.json"},
            ),
            (
                "Zabbix 主机资产插件",
                "asset_zabbix_host",
                "healthy",
                "已同步 2 台主机",
                {"script_command": "/opt/scripts/sync_zabbix.sh", "data_file": "/data/assets/zabbix.json"},
            ),
            (
                "IPMP 项目资产插件",
                "asset_ipmp_project",
                "warning",
                "等待 IPMP API 授权",
                {"script_command": "/opt/scripts/sync_ipmp.sh", "data_file": "/data/assets/ipmp.json"},
            ),
            (
                "工单主机资产插件",
                "asset_workorder_host",
                "healthy",
                "最近一次同步成功",
                {"script_command": "/opt/scripts/sync_workorder.sh", "data_file": "/data/assets/workorder.json"},
            ),
        ]

        for name, typ, status, message, cfg in config_specs:
            config, created = PluginConfig.objects.get_or_create(
                name=name,
                defaults={
                    "type": typ,
                    "enabled": True,
                    "status": status,
                    "last_message": message,
                    "config": cfg,
                    "created_by": admin_user,
                },
            )
            if not created:
                config.status = status
                config.last_message = message
                if cfg:
                    existing_cfg = config.config or {}
                    existing_cfg.update(cfg)
                    config.config = existing_cfg
                config.save(update_fields=["status", "last_message", "config", "updated_at"])
        self.stdout.write(" - 更新插件配置示例数据")

    def _ensure_assets(self, admin_user):
        asset_specs = [
            (AssetRecord.Source.CMDB, "svc-payment", "支付服务", "业务中台"),
            (AssetRecord.Source.ZABBIX, "host-redis-01", "Redis 节点", "缓存平台"),
            (AssetRecord.Source.PROMETHEUS, "k8s-node-03", "K8s 节点 03", "容器平台"),
        ]

        for source, external_id, name, system in asset_specs:
            record, created = AssetRecord.objects.get_or_create(
                source=source,
                external_id=external_id,
                defaults={
                    "name": name,
                    "system_name": system,
                    "metadata": {"demo": True},
                    "sync_status": "success",
                    "created_by": admin_user,
                },
            )
            if created:
                self.stdout.write(f" - 导入资产 {name}")

    def _ensure_audit_logs(self, admin_user):
        AuditLog.objects.filter(metadata__demo=True).delete()

        now = timezone.now()
        entries = [
            {
                "action": "settings.update",
                "target_type": "system.settings",
                "target_id": "platform",
                "result": "success",
                "metadata": {"demo": True, "fields": ["platform_name", "theme"]},
                "occurred_at": now - timedelta(minutes=30),
            },
            {
                "action": "monitoring.request.approve",
                "target_type": "monitoring.request",
                "target_id": "ITSMD-20240301-001",
                "result": "success",
                "metadata": {"demo": True, "approver": "demo-admin"},
                "occurred_at": now - timedelta(hours=2),
            },
            {
                "action": "assets.sync.trigger",
                "target_type": "assets.sync",
                "target_id": "manual",
                "result": "warning",
                "metadata": {"demo": True, "message": "部分资产重复"},
                "occurred_at": now - timedelta(days=1),
            },
        ]

        for entry in entries:
            AuditLog.objects.create(
                actor=admin_user,
                action=entry["action"],
                target_type=entry["target_type"],
                target_id=entry["target_id"],
                result=entry["result"],
                metadata=entry["metadata"],
                occurred_at=entry["occurred_at"],
                ip_address="10.0.0.10",
                user_agent="OneAll-Dashboard/1.0",
            )
        self.stdout.write(" - 写入审计日志样例")

    def _ensure_tools_and_knowledge(self, admin_user):
        repository_service = ScriptRepositoryService(actor=admin_user)
        tool, _ = ToolDefinition.objects.get_or_create(
            name="http-status-checker",
            defaults={
                "category": "诊断",
                "tags": ["HTTP", "检测"],
                "description": "通过 requests 库检测 HTTP 状态码并返回响应时间",
                "entry_point": "main.py",
                "default_parameters": {"url": "https://www.example.com"},
                "created_by": admin_user,
                "updated_by": admin_user,
            },
        )
        if tool.latest_version is None:
            repository_service.create_version(
                tool,
                content="""
import json
import time
import requests

def main(url: str):
    started = time.time()
    response = requests.get(url, timeout=5)
    duration = (time.time() - started) * 1000
    return json.dumps({"status_code": response.status_code, "elapsed_ms": duration}, ensure_ascii=False)
""",
                language=ScriptVersion.Language.PYTHON,
            )
            self.stdout.write(" - 新增工具 http-status-checker")

        KnowledgeArticle.objects.get_or_create(
            slug="http-status-checker-guide",
            defaults={
                "title": "HTTP 状态巡检脚本使用说明",
                "category": "工具库",
                "tags": ["工具", "http"],
                "content": "演示脚本用于检测指定 URL 的状态码及耗时。",
                "created_by": admin_user,
                "last_editor": admin_user,
            },
        )
        self.stdout.write(" - 创建知识库示例文章")
