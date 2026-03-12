from __future__ import annotations

from rest_framework import serializers

from apps.monitoring.models import DetectionTask


class MonitoringHistoryQuerySerializer(serializers.Serializer):
    target = serializers.CharField(required=False, allow_blank=True)
    status = serializers.ChoiceField(choices=DetectionTask.Status.choices, required=False)
    protocol = serializers.ChoiceField(choices=DetectionTask.Protocol.choices, required=False)
    probe_id = serializers.UUIDField(required=False)
    started_after = serializers.DateTimeField(required=False)
    started_before = serializers.DateTimeField(required=False)
    page = serializers.IntegerField(required=False, min_value=1, default=1)
    page_size = serializers.IntegerField(required=False, min_value=1, max_value=100, default=20)

    def validate(self, attrs):
        started_after = attrs.get("started_after")
        started_before = attrs.get("started_before")
        if started_after and started_before and started_after > started_before:
            raise serializers.ValidationError("started_after must be earlier than started_before")
        return attrs


class ProbeSummarySerializer(serializers.Serializer):
    id = serializers.UUIDField()
    name = serializers.CharField()
    location = serializers.CharField()
    network_type = serializers.CharField()
    status = serializers.CharField()


class MonitoringHistoryTaskSerializer(serializers.ModelSerializer):
    probe = serializers.SerializerMethodField()
    executed_at = serializers.SerializerMethodField()

    class Meta:
        model = DetectionTask
        fields = [
            "id",
            "target",
            "protocol",
            "status",
            "response_time_ms",
            "status_code",
            "error_message",
            "result_payload",
            "metadata",
            "executed_at",
            "created_at",
            "probe",
        ]
        read_only_fields = fields

    def get_probe(self, obj: DetectionTask):
        if not obj.probe:
            return None
        serializer = ProbeSummarySerializer(
            {
                "id": obj.probe.id,
                "name": obj.probe.name,
                "location": obj.probe.location,
                "network_type": obj.probe.network_type,
                "status": obj.probe.status,
            }
        )
        return serializer.data

    def get_executed_at(self, obj: DetectionTask):
        timestamp = obj.executed_at or obj.created_at
        return timestamp
