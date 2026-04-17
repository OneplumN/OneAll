from __future__ import annotations

from django.utils import timezone
from rest_framework import serializers

from apps.alerts.services import ensure_schedule_for_probe_schedule
from apps.monitoring.models import MonitoringRequest
from apps.probes.models import ProbeNode, ProbeSchedule, ProbeScheduleExecution
from apps.probes.services.certificate_schedule_service import sync_certificate_schedule_for_https


class ProbeNodeSerializer(serializers.ModelSerializer):
    ip_address = serializers.SerializerMethodField()

    class Meta:
        model = ProbeNode
        fields = [
            "id",
            "name",
            "location",
            "network_type",
            "supported_protocols",
            "status",
            "last_heartbeat_at",
            "last_authenticated_at",
            "api_token_hint",
            "ip_address",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "id",
            "created_at",
            "updated_at",
            "last_heartbeat_at",
            "last_authenticated_at",
            "api_token_hint",
        ]

    def get_ip_address(self, obj: ProbeNode) -> str | None:
        metrics = obj.runtime_metrics or {}
        value = metrics.get("ip_address")
        if isinstance(value, str) and value:
            return value
        return None


class ProbeTokenSerializer(serializers.Serializer):
    token = serializers.CharField(min_length=16, max_length=128)


class ProbeRegistrationSerializer(serializers.Serializer):
    hostname = serializers.CharField(max_length=255)
    ip_address = serializers.IPAddressField(required=False, allow_null=True)
    location = serializers.CharField(max_length=128, required=False, allow_blank=True)
    network_type = serializers.ChoiceField(
        choices=[choice[0] for choice in ProbeNode.NETWORK_TYPES],
        required=False,
    )
    supported_protocols = serializers.ListField(
        child=serializers.CharField(max_length=64),
        required=False,
        allow_empty=True,
    )
    agent_version = serializers.CharField(max_length=128, required=False, allow_blank=True)
    labels = serializers.DictField(
        child=serializers.CharField(max_length=256),
        required=False,
        allow_empty=True,
    )


class UpdateInstructionSerializer(serializers.Serializer):
    version = serializers.CharField(max_length=128)
    download_url = serializers.URLField()
    sha256 = serializers.CharField(required=False, allow_blank=True, max_length=128)


class ProbeAgentConfigSerializer(serializers.Serializer):
    version = serializers.CharField(required=False, allow_blank=True, max_length=128)
    heartbeat_interval = serializers.IntegerField(min_value=1, required=False)
    task_poll_interval = serializers.IntegerField(min_value=1, required=False)
    max_concurrent_tasks = serializers.IntegerField(min_value=1, required=False)
    enabled_protocols = serializers.ListField(child=serializers.CharField(), required=False)
    log_level = serializers.CharField(required=False, allow_blank=True, max_length=32)
    update = UpdateInstructionSerializer(required=False)


class MonitoringRequestSummarySerializer(serializers.ModelSerializer):
    class Meta:
        model = MonitoringRequest
        fields = [
            "id",
            "title",
            "status",
            "itsm_ticket_id",
            "frequency_minutes",
        ]
        read_only_fields = fields


class ProbeScheduleSummarySerializer(serializers.ModelSerializer):
    status_display = serializers.CharField(source="get_status_display", read_only=True)
    source_display = serializers.CharField(source="get_source_type_display", read_only=True)

    class Meta:
        model = ProbeSchedule
        fields = [
            "id",
            "name",
            "target",
            "protocol",
            "frequency_minutes",
            "status",
            "status_display",
            "source_type",
            "source_display",
        ]
        read_only_fields = fields


class ProbeScheduleSerializer(serializers.ModelSerializer):
    probes = ProbeNodeSerializer(many=True, read_only=True)
    probe_ids = serializers.ListField(child=serializers.UUIDField(), write_only=True, required=False)
    status_display = serializers.CharField(source="get_status_display", read_only=True)
    source_display = serializers.CharField(source="get_source_type_display", read_only=True)
    monitoring_request = MonitoringRequestSummarySerializer(read_only=True)
    start_at = serializers.DateTimeField(required=False, allow_null=True)
    end_at = serializers.DateTimeField(required=False, allow_null=True)
    timeout_seconds = serializers.IntegerField(required=False, min_value=1, write_only=True)
    expected_status_codes = serializers.ListField(
        child=serializers.IntegerField(min_value=100, max_value=599),
        required=False,
        allow_empty=True,
        write_only=True,
    )
    alert_threshold = serializers.IntegerField(required=False, min_value=1, write_only=True)
    alert_contacts = serializers.ListField(
        child=serializers.CharField(allow_blank=False, max_length=64),
        required=False,
        allow_empty=True,
        write_only=True,
    )
    alert_channels = serializers.ListField(
        child=serializers.CharField(allow_blank=False, max_length=64),
        required=False,
        allow_empty=True,
        write_only=True,
    )
    cert_check_enabled = serializers.BooleanField(required=False, write_only=True)
    cert_warning_days = serializers.IntegerField(required=False, min_value=1, max_value=365, write_only=True)

    class Meta:
        model = ProbeSchedule
        fields = [
            "id",
            "name",
            "description",
            "target",
            "protocol",
            "frequency_minutes",
            "start_at",
            "end_at",
            "status",
            "status_display",
            "status_reason",
            "source_type",
            "source_display",
            "source_id",
            "metadata",
            "monitoring_request",
            "monitoring_job",
            "last_run_at",
            "next_run_at",
            "created_at",
            "updated_at",
            "probes",
            "probe_ids",
            "start_at",
            "end_at",
            "timeout_seconds",
            "expected_status_codes",
            "alert_threshold",
            "alert_contacts",
            "alert_channels",
            "cert_check_enabled",
            "cert_warning_days",
        ]
        read_only_fields = [
            "id",
            "status",
            "status_display",
            "status_reason",
            "source_type",
            "source_display",
            "source_id",
            "metadata",
            "monitoring_request",
            "monitoring_job",
            "last_run_at",
            "next_run_at",
            "created_at",
            "updated_at",
            "probes",
        ]

    def validate_frequency_minutes(self, value: int) -> int:
        if value < 1:
            raise serializers.ValidationError("频率必须 >= 1 分钟")
        return value

    def create(self, validated_data):
        probe_ids = validated_data.pop("probe_ids", None) or []
        if not probe_ids:
            raise serializers.ValidationError({"probe_ids": "至少选择一个探针节点"})
        validated_data.pop("metadata", None)
        metadata_updates = self._pop_metadata_fields(validated_data)
        start_at = validated_data.get("start_at") or timezone.now()
        validated_data.setdefault("start_at", start_at)
        validated_data.setdefault("next_run_at", start_at)
        schedule = ProbeSchedule.objects.create(metadata=metadata_updates or {}, **validated_data)
        self._assign_probes(schedule, probe_ids)
        # 手工探针调度创建时，生成对应的 AlertCheck / AlertSchedule，方便中央调度接管。
        ensure_schedule_for_probe_schedule(schedule)
        # 若为 HTTPS 手工策略，按需同步配对的 CERTIFICATE 调度（证书检测）。
        sync_certificate_schedule_for_https(schedule)
        return schedule

    def _assign_probes(self, schedule: ProbeSchedule, probe_ids: list) -> None:
        probes = ProbeNode.objects.filter(id__in=probe_ids)
        schedule.probes.set(probes)

    def update(self, instance, validated_data):
        probe_ids = validated_data.pop("probe_ids", None)
        metadata_updates = self._pop_metadata_fields(validated_data)
        validated_data.pop("metadata", None)
        schedule = super().update(instance, validated_data)
        if metadata_updates:
            current = dict(schedule.metadata or {})
            current.update(metadata_updates)
            schedule.metadata = current
            schedule.save(update_fields=["metadata", "updated_at"])
        if probe_ids is not None:
            if schedule.source_type != ProbeSchedule.Source.MANUAL:
                raise serializers.ValidationError({"probe_ids": "非手工调度不支持修改探针"})
            self._assign_probes(schedule, probe_ids)
        # 更新手工策略后，无论改的是基础字段还是 metadata，都同步刷新 alerts 映射与证书配对策略。
        ensure_schedule_for_probe_schedule(schedule)
        sync_certificate_schedule_for_https(schedule)
        return schedule

    def to_representation(self, instance):
        data = super().to_representation(instance)
        metadata = instance.metadata or {}
        data["timeout_seconds"] = metadata.get("timeout_seconds")
        data["expected_status_codes"] = metadata.get("expected_status_codes") or []
        data["alert_threshold"] = metadata.get("alert_threshold")
        data["alert_contacts"] = metadata.get("alert_contacts") or []
        data["alert_channels"] = metadata.get("alert_channels") or []
        data["cert_check_enabled"] = metadata.get("cert_check_enabled", False)
        data["cert_warning_days"] = metadata.get("cert_warning_days")
        return data

    def _pop_metadata_fields(self, validated_data: dict) -> dict:
        metadata: dict = {}
        timeout_seconds = validated_data.pop("timeout_seconds", None)
        if timeout_seconds is not None:
            metadata["timeout_seconds"] = int(timeout_seconds)

        expected_codes = validated_data.pop("expected_status_codes", None)
        if expected_codes is not None:
            normalized = sorted({int(code) for code in expected_codes if 100 <= int(code) <= 599})
            metadata["expected_status_codes"] = normalized if normalized else [200]

        alert_threshold = validated_data.pop("alert_threshold", None)
        if alert_threshold is not None:
            metadata["alert_threshold"] = int(alert_threshold)

        alert_contacts = validated_data.pop("alert_contacts", None)
        if alert_contacts is not None:
            cleaned = [contact.strip() for contact in alert_contacts if contact]
            metadata["alert_contacts"] = cleaned

        alert_channels = validated_data.pop("alert_channels", None)
        if alert_channels is not None:
            cleaned_channels = [
                str(channel).strip() for channel in alert_channels if str(channel).strip()
            ]
            if cleaned_channels:
                metadata["alert_channels"] = cleaned_channels

        cert_enabled = validated_data.pop("cert_check_enabled", None)
        if cert_enabled is not None:
            metadata["cert_check_enabled"] = bool(cert_enabled)

        cert_warning_days = validated_data.pop("cert_warning_days", None)
        if cert_warning_days is not None:
            days = int(cert_warning_days)
            metadata["cert_warning_days"] = days
            # 同时写入通用的 warning_threshold_days，方便 CERTIFICATE 探针直接读取。
            metadata["warning_threshold_days"] = days

        return metadata


class ProbeScheduleExecutionSerializer(serializers.ModelSerializer):
    schedule_id = serializers.UUIDField(source="schedule.id", read_only=True)
    probe = ProbeNodeSerializer(read_only=True)
    schedule = ProbeScheduleSummarySerializer(read_only=True)

    class Meta:
        model = ProbeScheduleExecution
        fields = [
            "id",
            "schedule_id",
            "schedule",
            "probe",
            "scheduled_at",
            "started_at",
            "finished_at",
            "status",
            "response_time_ms",
            "status_code",
            "message",
            "metadata",
            "created_at",
            "updated_at",
        ]
        read_only_fields = fields

    def to_representation(self, instance):
        data = super().to_representation(instance)
        status_value = data.get("status")
        if status_value:
            data["status"] = ProbeScheduleExecution.normalize_status(status_value)
        return data

    def update(self, instance, validated_data):
        probe_ids = validated_data.pop("probe_ids", None)
        metadata_updates = self._pop_metadata_fields(validated_data)
        validated_data.pop("metadata", None)
        schedule = super().update(instance, validated_data)
        if metadata_updates:
            current = dict(schedule.metadata or {})
            current.update(metadata_updates)
            schedule.metadata = current
            schedule.save(update_fields=["metadata", "updated_at"])
        if probe_ids is not None:
            if schedule.source_type != ProbeSchedule.Source.MANUAL:
                raise serializers.ValidationError({"probe_ids": "非手工调度不支持修改探针"})
            self._assign_probes(schedule, probe_ids)
        return schedule
