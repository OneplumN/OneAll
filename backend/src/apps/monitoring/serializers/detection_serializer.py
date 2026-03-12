from __future__ import annotations

from rest_framework import serializers

from apps.monitoring.models import DetectionTask


class DetectionRequestSerializer(serializers.Serializer):
    target = serializers.URLField()
    protocol = serializers.ChoiceField(choices=DetectionTask.Protocol.choices)
    probe_id = serializers.UUIDField(required=False, allow_null=True)
    timeout_seconds = serializers.IntegerField(min_value=1, max_value=300, default=30)
    metadata = serializers.JSONField(required=False)


class DetectionTaskSerializer(serializers.ModelSerializer):
    class Meta:
        model = DetectionTask
        fields = [
            'id',
            'target',
            'protocol',
            'status',
            'response_time_ms',
            'status_code',
            'error_message',
            'result_payload',
            'metadata',
            'executed_at',
            'created_at',
        ]
        read_only_fields = fields
