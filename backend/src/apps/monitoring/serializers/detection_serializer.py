from __future__ import annotations

import ipaddress
from urllib.parse import urlparse

from rest_framework import serializers

from apps.monitoring.models import DetectionTask


class DetectionRequestSerializer(serializers.Serializer):
    target = serializers.CharField(max_length=512)
    protocol = serializers.ChoiceField(choices=DetectionTask.Protocol.choices)
    probe_id = serializers.UUIDField()
    timeout_seconds = serializers.IntegerField(min_value=1, max_value=300, default=30)
    metadata = serializers.JSONField(required=False)

    def validate(self, attrs):
        attrs = super().validate(attrs)
        target = (attrs.get("target") or "").strip()
        protocol = attrs.get("protocol")

        if not target:
            raise serializers.ValidationError({"target": "请输入目标地址"})

        validator = _PROTOCOL_VALIDATORS.get(protocol)
        if validator:
            validator(target)
        attrs["target"] = target
        return attrs


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


def _validate_http_target(target: str) -> None:
    parsed = urlparse(target)
    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        raise serializers.ValidationError({"target": "请输入包含 http:// 或 https:// 的完整地址"})


def _validate_wss_target(target: str) -> None:
    parsed = urlparse(target)
    if parsed.scheme not in {"ws", "wss"} or not parsed.netloc:
        raise serializers.ValidationError({"target": "请输入有效的 WebSocket 地址"})


def _validate_host_target(target: str) -> None:
    host = target.strip()
    if host.startswith("[") and "]" in host:
        host = host[1 : host.index("]")]
    elif host.count(":") == 1 and not host.endswith("]"):
        host = host.rsplit(":", 1)[0]

    if not host:
        raise serializers.ValidationError({"target": "请输入有效的域名或 IP 地址"})

    try:
        ipaddress.ip_address(host)
        return
    except ValueError:
        pass

    labels = host.split(".")
    if len(labels) < 2:
        raise serializers.ValidationError({"target": "请输入有效的域名或 IP 地址"})
    for label in labels:
        if not label or len(label) > 63:
            raise serializers.ValidationError({"target": "请输入有效的域名或 IP 地址"})
        if label.startswith("-") or label.endswith("-"):
            raise serializers.ValidationError({"target": "请输入有效的域名或 IP 地址"})
        if not all(ch.isalnum() or ch == "-" for ch in label):
            raise serializers.ValidationError({"target": "请输入有效的域名或 IP 地址"})


_PROTOCOL_VALIDATORS = {
    DetectionTask.Protocol.HTTP: _validate_http_target,
    DetectionTask.Protocol.HTTPS: _validate_http_target,
    DetectionTask.Protocol.CERTIFICATE: _validate_http_target,
    DetectionTask.Protocol.WSS: _validate_wss_target,
    DetectionTask.Protocol.TELNET: _validate_host_target,
    DetectionTask.Protocol.TCP: _validate_host_target,
}
