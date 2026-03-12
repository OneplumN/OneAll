from __future__ import annotations

from rest_framework import serializers

from apps.monitoring.models import MonitoringJob, MonitoringRequest


class MonitoringJobSerializer(serializers.ModelSerializer):
    class Meta:
        model = MonitoringJob
        fields = [
            "id",
            "status",
            "schedule_cron",
            "frequency_minutes",
            "last_run_at",
            "next_run_at",
        ]
        read_only_fields = fields


class MonitoringRequestSerializer(serializers.ModelSerializer):
    jobs = MonitoringJobSerializer(many=True, read_only=True)
    expected_status_codes = serializers.SerializerMethodField()
    created_by_id = serializers.SerializerMethodField()
    created_by_username = serializers.SerializerMethodField()

    class Meta:
        model = MonitoringRequest
        fields = [
            "id",
            "title",
            "target",
            "protocol",
            "description",
            "status",
            "frequency_minutes",
            "schedule_cron",
            "itsm_ticket_id",
            "metadata",
            "expected_status_codes",
            "created_at",
            "updated_at",
            "jobs",
            "created_by_id",
            "created_by_username",
        ]
        read_only_fields = [
            "id",
            "status",
            "itsm_ticket_id",
            "metadata",
            "expected_status_codes",
            "created_at",
            "updated_at",
            "jobs",
            "created_by_id",
            "created_by_username",
        ]

    def get_expected_status_codes(self, obj: MonitoringRequest) -> list[int]:
        metadata = obj.metadata or {}
        codes = metadata.get("expected_status_codes") or []
        if not isinstance(codes, list):
            return []
        normalized: list[int] = []
        for code in codes:
            try:
                value = int(code)
            except (TypeError, ValueError):
                continue
            normalized.append(value)
        return normalized

    def get_created_by_id(self, obj: MonitoringRequest) -> str | None:
        if not obj.created_by_id:
            return None
        return str(obj.created_by_id)

    def get_created_by_username(self, obj: MonitoringRequest) -> str:
        user = getattr(obj, "created_by", None)
        if not user:
            return ""
        return str(getattr(user, "username", "") or "")


class MonitoringRequestCreateSerializer(serializers.ModelSerializer):
    system_name = serializers.CharField(required=False, allow_blank=True)
    network_type = serializers.ChoiceField(
        choices=(
            ("internal", "internal"),
            ("internet", "internet"),
        ),
        required=False,
    )
    owner_name = serializers.CharField(required=False, allow_blank=True)
    alert_contacts = serializers.ListField(
        child=serializers.CharField(allow_blank=False),
        required=False,
        allow_empty=True,
    )
    probe_ids = serializers.ListField(
        child=serializers.UUIDField(),
        required=False,
        allow_empty=True,
    )
    alert_threshold = serializers.IntegerField(required=False, min_value=1)
    expected_status_codes = serializers.ListField(
        child=serializers.IntegerField(min_value=100, max_value=599),
        required=False,
        allow_empty=True,
    )

    class Meta:
        model = MonitoringRequest
        fields = [
            "title",
            "target",
            "protocol",
            "description",
            "frequency_minutes",
            "schedule_cron",
            "metadata",
            "system_name",
            "network_type",
            "owner_name",
            "alert_contacts",
            "probe_ids",
            "alert_threshold",
            "expected_status_codes",
        ]
        extra_kwargs = {
            "metadata": {"required": False},
        }

    def validate_expected_status_codes(self, value: list[int] | None) -> list[int]:
        if not value:
            return [200]
        normalized = sorted({int(code) for code in value})
        return normalized

    def create(self, validated_data):
        metadata = dict(validated_data.pop("metadata", {}) or {})
        if "expected_status_codes" not in validated_data:
            validated_data["expected_status_codes"] = [200]

        def _store(key: str, transform=lambda x: x):
            value = validated_data.pop(key, None)
            if value in (None, "", []):
                return
            metadata[key] = transform(value)

        _store("system_name")
        _store("network_type")
        _store("owner_name")
        _store("alert_contacts")
        _store("probe_ids", lambda values: [str(v) for v in values])
        _store("alert_threshold")
        _store("expected_status_codes")

        validated_data["metadata"] = metadata
        return MonitoringRequest.objects.create(**validated_data)


class MonitoringRequestUpdateSerializer(serializers.ModelSerializer):
    system_name = serializers.CharField(required=False, allow_blank=True)
    network_type = serializers.ChoiceField(
        choices=(
            ("internal", "internal"),
            ("internet", "internet"),
        ),
        required=False,
    )
    owner_name = serializers.CharField(required=False, allow_blank=True)
    alert_contacts = serializers.ListField(
        child=serializers.CharField(allow_blank=False),
        required=False,
        allow_empty=True,
    )
    probe_ids = serializers.ListField(
        child=serializers.UUIDField(),
        required=False,
        allow_empty=True,
    )
    alert_threshold = serializers.IntegerField(required=False, min_value=1)
    expected_status_codes = serializers.ListField(
        child=serializers.IntegerField(min_value=100, max_value=599),
        required=False,
        allow_empty=True,
    )

    class Meta:
        model = MonitoringRequest
        fields = [
            "title",
            "target",
            "protocol",
            "description",
            "frequency_minutes",
            "schedule_cron",
            "metadata",
            "system_name",
            "network_type",
            "owner_name",
            "alert_contacts",
            "probe_ids",
            "alert_threshold",
            "expected_status_codes",
        ]
        extra_kwargs = {
            "metadata": {"required": False},
        }

    def validate_expected_status_codes(self, value: list[int] | None) -> list[int]:
        if not value:
            return [200]
        normalized = sorted({int(code) for code in value})
        return normalized

    def update(self, instance: MonitoringRequest, validated_data: dict) -> MonitoringRequest:
        metadata = dict(instance.metadata or {})
        incoming_meta = dict(validated_data.pop("metadata", {}) or {})
        metadata.update(incoming_meta)

        def _store(key: str, transform=lambda x: x):
            if key not in validated_data:
                return
            value = validated_data.pop(key)
            if value in (None, "", []):
                metadata.pop(key, None)
                return
            metadata[key] = transform(value)

        _store("system_name")
        _store("network_type")
        _store("owner_name")
        _store("alert_contacts")
        _store("probe_ids", lambda values: [str(v) for v in values])
        _store("alert_threshold")
        _store("expected_status_codes")

        for field in ["title", "target", "protocol", "description", "frequency_minutes", "schedule_cron"]:
            if field in validated_data:
                setattr(instance, field, validated_data[field])

        instance.metadata = metadata
        instance.save()
        return instance
